import { Controller, Get, PathParams, Post, BodyParams } from '@tsed/common'
import { NotFound } from '@tsed/exceptions'
import {
  JsonTransformer,
  ProofExchangeRecord,
  AgentConfig,
  Logger,
  ProofEventTypes,
  ProofStateChangedEvent,
  ProofState,
} from '@credo-ts/core'
import { ProofUtils } from '../utils/ProofUtils'
import { filter, firstValueFrom, ReplaySubject, timeout } from 'rxjs'
import util from 'util'
import { BaseController } from '../BaseController'
import { TestHarnessConfig } from '../TestHarnessConfig'
import { ConnectionUtils } from '../utils/ConnectionUtils'
// TODO: have to change that V1PresentationPreview to something else
import { V1PresentationPreview, AnonCredsProofRequest, AnonCredsRequestedAttributeMatch, AnonCredsRequestedPredicateMatch } from '@credo-ts/anoncreds'
@Controller('/agent/command/proof-v2')
export class PresentProofController extends BaseController {
  private logger: Logger
  private subject = new ReplaySubject<ProofStateChangedEvent>()

  public constructor(testHarnessConfig: TestHarnessConfig) {
    super(testHarnessConfig)

    this.logger = this.agent.dependencyManager.resolve(AgentConfig).logger
  }

  public onStartup() {
    this.subject = new ReplaySubject<ProofStateChangedEvent>()
    // Catch all events in replay subject for later use
    this.agent.events.observable<ProofStateChangedEvent>(ProofEventTypes.ProofStateChanged).subscribe(this.subject)
  }

  @Get('/:threadId')
  async getProofByThreadId(@PathParams('threadId') threadId: string) {
    const proofRecord = await ProofUtils.getProofByThreadId(this.agent, threadId)

    if (!proofRecord) {
      throw new NotFound(`proof record for thead id "${threadId}" not found.`)
    }

    return this.mapProofExchangeRecord(proofRecord)
  }

  @Get('/')
  async getAllProofs() {
    const proofs = await this.agent.proofs.getAll()

    return proofs.map((proof) => this.mapProofExchangeRecord(proof))
  }

  @Post('/send-proposal')
  async sendProposal(
    @BodyParams('data')
    data: {
      connection_id: string
      presentation_proposal: {
        comment?: string
        attributes: any
        predicates: any
      }
    }
  ) {

    const presentationProposal = JsonTransformer.fromJSON(data.presentation_proposal, V1PresentationPreview)
    const { attributes, predicates } = presentationProposal

    const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, data.connection_id)

    const proofRecord = await this.agent.proofs.proposeProof({
      connectionId: connection.id, 
      protocolVersion: 'v2',
      proofFormats: {
        indy: {
          attributes,
          predicates,
        },
      },
      comment: data.presentation_proposal.comment
    })

    return this.mapProofExchangeRecord(proofRecord)
  }

  @Post('/send-request')
  async sendRequest(
    @BodyParams('id') threadId: string,
    @BodyParams('data')
    data: {
      connection_id: string
      presentation_request: {
        comment?: string
        proof_request: {
          data: unknown
        }
      }
    }
  ) {

    this.logger.info('Sending request', {
      proofRequest: util.inspect(data.presentation_request.proof_request, { showHidden: false, depth: null }),
    })
    // Do not validate, we only need a few properties from the proof request
    const proofRequest = data.presentation_request.proof_request.data as AnonCredsProofRequest

    const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, data.connection_id)

    // TODO: AFJ doesn't support to negotiate proposal yet
    // if thread id is present
    const proofRecord = await this.agent.proofs.requestProof({
      connectionId: connection.id,
      protocolVersion: 'v2',
      proofFormats: {
        indy: {
          name: proofRequest.name ?? 'proof-request',
          version: proofRequest.version ?? '2.0',
          non_revoked: proofRequest.non_revoked,
          requested_attributes: proofRequest.requested_attributes,
          requested_predicates: proofRequest.requested_predicates  
        }
      },
      comment: data.presentation_request.comment,
    })

    return this.mapProofExchangeRecord(proofRecord)
  }

  @Post('/send-presentation')
  async sendPresentation(
    @BodyParams('id') threadId: string,
    @BodyParams('data')
    data: {
      self_attested_attributes: Record<string, string>
      requested_attributes: Record<string, { cred_id: string; timestamp?: number; revealed: boolean }>
      requested_predicates: Record<string, { cred_id: string; revealed: boolean }>
      comment: string
    }
  ) {
    await this.waitForState(threadId, ProofState.RequestReceived)
    let proofRecord = await ProofUtils.getProofByThreadId(this.agent, threadId)

    const retrievedCredentials = await this.agent.proofs.getCredentialsForRequest({
      proofRecordId: proofRecord.id, 
      // Some tests include presenting a revoked credential, expecting the verification to fail
      // So not excluding those from the retrieved credentials.
      proofFormats: {indy: {filterByNonRevocationRequirements: false }}
    })

    let attributes: Record<string, AnonCredsRequestedAttributeMatch> = {}
    let predicates: Record<string, AnonCredsRequestedPredicateMatch> = {}
    
    if (data.requested_attributes) {
      Object.keys(data.requested_attributes).forEach((key) => {
        attributes[key] = retrievedCredentials.proofFormats.indy?.attributes[key]?.find(
          (a) => a.credentialId === data.requested_attributes[key].cred_id
        ) as AnonCredsRequestedAttributeMatch
      })
    }
    if (data.requested_predicates) {
      Object.keys(data.requested_predicates).forEach((key) => {
        predicates[key]  = retrievedCredentials.proofFormats.indy?.predicates[key].find(
          (p) => p.credentialId ===  data.requested_predicates[key].cred_id
        ) as AnonCredsRequestedPredicateMatch
      })
    }

    this.logger.info('Created proof request', {
      attributes: util.inspect(attributes, { showHidden: false, depth: null }),
      predicates: util.inspect(predicates, { showHidden: false, depth: null }),
      retrievedCredentials: util.inspect(retrievedCredentials, { showHidden: false, depth: null }),
    })

    proofRecord = await this.agent.proofs.acceptRequest({ 
      proofRecordId: proofRecord.id, 
      proofFormats: { indy: { attributes, predicates, selfAttestedAttributes: {} } },
      comment: data.comment,
    })

    return this.mapProofExchangeRecord(proofRecord)
  }

  @Post('/verify-presentation')
  async verifyPresentation(@BodyParams('id') threadId: string) {
    await this.waitForState(threadId, ProofState.PresentationReceived)

    let proofRecord = await ProofUtils.getProofByThreadId(this.agent, threadId)
    if (proofRecord) {
      return this.mapProofExchangeRecord(await this.agent.proofs.acceptPresentation({ proofRecordId: proofRecord.id }))
    }
  }

  private async waitForState(threadId: string, state: ProofState) {
    return await firstValueFrom(
      this.subject.pipe(
        filter((c) => c.payload.proofRecord.threadId === threadId),
        filter((c) => c.payload.proofRecord.state === state),
        timeout(20000)
      )
    )
  }

  private mapProofExchangeRecord(proofExchangeRecord: ProofExchangeRecord) {
    return {
      state: proofExchangeRecord.state,
      thread_id: proofExchangeRecord.threadId,
    }
  }
}
