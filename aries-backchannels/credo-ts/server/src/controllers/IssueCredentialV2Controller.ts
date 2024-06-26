import { BodyParams, Controller, Get, PathParams, Post } from '@tsed/common'
import { BadRequest, NotFound } from '@tsed/exceptions'
import {
  CredentialEventTypes,
  CredentialExchangeRecord,
  CredentialState,
  CredentialStateChangedEvent,
  JsonTransformer,
  V2CredentialPreview,
} from '@credo-ts/core'
import { CredentialUtils } from '../utils/CredentialUtils'
import { filter, firstValueFrom, ReplaySubject, timeout } from 'rxjs'
import { BaseController } from '../BaseController'
import { TestHarnessConfig } from '../TestHarnessConfig'
import { ConnectionUtils } from '../utils/ConnectionUtils'

const afjFormatToAathFormatMapping: Record<string, string> = {
  indy: 'indy',
  anoncreds: 'indy',
}

@Controller('/agent/command/issue-credential-v2')
export class IssueCredentialV2Controller extends BaseController {
  private subject = new ReplaySubject<CredentialStateChangedEvent>()

  public constructor(testHarnessConfig: TestHarnessConfig) {
    super(testHarnessConfig)
  }

  public onStartup() {
    this.subject = new ReplaySubject<CredentialStateChangedEvent>()
    // Catch all events in replay subject for later use
    this.agent.events
      .observable<CredentialStateChangedEvent>(CredentialEventTypes.CredentialStateChanged)
      .subscribe(this.subject)
  }

  @Get('/:threadId')
  async getCredentialByThreadId(@PathParams('threadId') threadId: string) {
    const credential = await CredentialUtils.getCredentialByThreadId(this.agent, threadId)
    if (!credential) {
      throw new NotFound(`credential for thead id "${threadId}" not found.`)
    }
    return this.mapCredential(credential)
  }

  @Get('/')
  async getAllCredentials() {
    const credentials = await this.agent.credentials.getAll()

    return credentials.map((cred) => this.mapCredential(cred))
  }

  @Post('/send-proposal')
  async sendProposal(
    @BodyParams('data')
    data: {
      connection_id: string
      filter: {
        indy: {
          schema_issuer_did?: string
          issuer_did?: string
          schema_name?: string
          cred_def_id?: string
          schema_version?: string
          schema_id?: string
        }
      }
      credential_preview: any
    }
  ) {
    // Disable validation. the @type sent by AATH is 'issue-credential/2.0/credential-preview'
    // which is not a valid message type.
    const preview = JsonTransformer.fromJSON(data.credential_preview, V2CredentialPreview, { validate: false })
    const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, data.connection_id)
    const credentialRecord = await this.agent.credentials.proposeCredential({
      connectionId: connection.id,
      protocolVersion: 'v2',
      credentialFormats: {
        indy: {
          attributes: preview.attributes,
          schemaIssuerDid: data.filter.indy.schema_issuer_did,
          issuerDid: data.filter.indy.issuer_did,
          schemaName: data.filter.indy.schema_name,
          credentialDefinitionId: data.filter.indy.cred_def_id,
          schemaVersion: data.filter.indy.schema_version,
          schemaId: data.filter.indy.schema_id,
        },
      },
    })

    return this.mapCredential(credentialRecord)
  }

  @Post('/send-offer')
  async sendOffer(
    @BodyParams('id') threadId?: string,
    @BodyParams('data')
    data?: {
      connection_id: string
      filter: {
        indy: {
          schema_issuer_did?: string
          issuer_did?: string
          schema_name?: string
          cred_def_id?: string
          schema_version?: string
          schema_id?: string
        }
      }
      credential_preview: any
    }
  ) {
    let credentialRecord: CredentialExchangeRecord

    this.agent.config.logger.info('Sending credential offer', data)

    if (threadId) {
      await this.waitForState(threadId, CredentialState.ProposalReceived)
      let credentialRecord = await CredentialUtils.getCredentialByThreadId(this.agent, threadId)

      this.agent.config.logger.info('Replying to credential proposal')

      credentialRecord = await this.agent.credentials.acceptProposal({
        credentialRecordId: credentialRecord.id,
      })
      return this.mapCredential(credentialRecord)
    } else if (data) {
      // Disable validation. the @type sent by AATH is 'issue-credential/2.0/credential-preview'
      // which is not a valid message type.
      const preview = JsonTransformer.fromJSON(data.credential_preview, V2CredentialPreview, { validate: false })
      const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, data.connection_id)

      if (!data.filter.indy.cred_def_id) {
        throw new BadRequest('data.filter.indy.cred_def_id is required')
      }

      credentialRecord = await this.agent.credentials.offerCredential({
        connectionId: connection.id,
        protocolVersion: 'v2',
        credentialFormats: {
          indy: {
            attributes: preview.attributes,
            credentialDefinitionId: data.filter.indy.cred_def_id,
          },
        },
      })
      return this.mapCredential(credentialRecord)
    } else {
      throw new BadRequest(`Missing both id and data properties`)
    }
  }

  @Post('/send-request')
  async sendRequest(@BodyParams('id') threadId: string) {
    await this.waitForState(threadId, CredentialState.OfferReceived)
    let { id } = await CredentialUtils.getCredentialByThreadId(this.agent, threadId)

    const credentialRecord = await this.agent.credentials.acceptOffer({
      credentialRecordId: id,
    })
    return this.mapCredential(credentialRecord)
  }

  @Post('/issue')
  async acceptRequest(@BodyParams('id') threadId: string, @BodyParams('data') data?: { comment?: string }) {
    await this.waitForState(threadId, CredentialState.RequestReceived)
    const { id } = await CredentialUtils.getCredentialByThreadId(this.agent, threadId)

    const credentialRecord = await this.agent.credentials.acceptRequest({
      credentialRecordId: id,
      comment: data?.comment,
    })
    return this.mapCredential(credentialRecord)
  }

  @Post('/store')
  async storeCredential(@BodyParams('id') threadId: string) {
    await this.waitForState(threadId, CredentialState.CredentialReceived)
    let { id } = await CredentialUtils.getCredentialByThreadId(this.agent, threadId)
    const credentialRecord = await this.agent.credentials.acceptCredential({ credentialRecordId: id })

    return this.mapCredential(credentialRecord)
  }

  private async waitForState(threadId: string, state: CredentialState) {
    return await firstValueFrom(
      this.subject.pipe(
        filter((c) => c.payload.credentialRecord.threadId === threadId),
        filter((c) => c.payload.credentialRecord.state === state),
        timeout(20000)
      )
    )
  }

  private mapCredential(credentialRecord: CredentialExchangeRecord) {
    let returnModel = {
      state: credentialRecord.state,
      thread_id: credentialRecord.threadId,
    }

    for (const credential of credentialRecord.credentials) {
      const key = afjFormatToAathFormatMapping[credential.credentialRecordType]

      returnModel = {
        ...returnModel,
        [key]: {
          credential_id: credential.credentialRecordId,
        },
      }
    }

    return returnModel
  }
}
