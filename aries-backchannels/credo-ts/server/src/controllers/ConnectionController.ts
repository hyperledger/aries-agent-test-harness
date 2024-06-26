import { Controller, Get, PathParams, Post, BodyParams } from '@tsed/common'
import { NotFound } from '@tsed/exceptions'
import {
  ConnectionRecord,
  ConnectionInvitationMessage,
  JsonTransformer,
  AgentConfig,
  ConnectionEventTypes,
  ConnectionStateChangedEvent,
  ConnectionState,
  CredoError,
  DidExchangeState,
} from '@credo-ts/core'

import { convertToNewInvitation } from '@credo-ts/core/build/modules/oob/helpers'
import { filter, firstValueFrom, ReplaySubject, tap, timeout } from 'rxjs'
import { BaseController } from '../BaseController'
import { TestHarnessConfig } from '../TestHarnessConfig'
import { ConnectionUtils } from '../utils/ConnectionUtils'

@Controller('/agent/command/connection')
export class ConnectionController extends BaseController {
  private subject = new ReplaySubject<ConnectionStateChangedEvent>()

  public constructor(testHarnessConfig: TestHarnessConfig) {
    super(testHarnessConfig)
  }

  onStartup = () => {
    this.subject = new ReplaySubject<ConnectionStateChangedEvent>()
    // Catch all events in replay subject for later use
    this.agent.events
      .observable<ConnectionStateChangedEvent>(ConnectionEventTypes.ConnectionStateChanged)
      .subscribe(this.subject)
  }

  @Get('/:id')
  async getConnectionById(@PathParams('id') id: string) {
    const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, id)

    if (!connection) throw new NotFound(`Connection with id ${id} not found`)

    return this.mapConnection(connection)
  }

  @Get('/')
  async getAllConnections() {
    const connections = await this.agent.connections.getAll()

    return connections.map((conn) => this.mapConnection(conn))
  }

  @Post('/create-invitation')
  async createInvitation(@BodyParams('data') data?: { mediator_connection_id?: string }) {
    const mediatorId = await this.mediatorIdFromMediatorConnectionId(data?.mediator_connection_id)

    const routing = await this.agent.mediationRecipient.getRouting({
      mediatorId,
    })

    const { invitation, outOfBandRecord } = await this.agent.oob.createLegacyInvitation({
      routing,
      // Needed to complete connection: https://github.com/hyperledger/aries-framework-javascript/issues/668
      autoAcceptConnection: true,
    })

    const config = this.agent.dependencyManager.resolve(AgentConfig)
    const invitationJson = invitation.toJSON({ useDidSovPrefixWhereAllowed: config.useDidSovPrefixWhereAllowed })

    return {
      state: ConnectionState.Invited,
      // This should be the connection id. However, the connection id is not available until a request is received.
      // We can just use the oob invitation I guess.
      connection_id: outOfBandRecord.id,
      invitation: invitationJson,
    }
  }

  @Post('/receive-invitation')
  async receiveInvitation(@BodyParams('data') data: Record<string, unknown> & { mediator_connection_id?: string }) {
    const { mediator_connection_id, ...invitationJson } = data

    const mediatorId = await this.mediatorIdFromMediatorConnectionId(mediator_connection_id)

    const routing = await this.agent.mediationRecipient.getRouting({
      mediatorId,
    })

    const oobInvitation = convertToNewInvitation(JsonTransformer.fromJSON(invitationJson, ConnectionInvitationMessage))
    const { connectionRecord } = await this.agent.oob.receiveInvitation(oobInvitation, {
      routing,
      // Needed to complete connection: https://github.com/hyperledger/aries-framework-javascript/issues/668
      autoAcceptConnection: true,
      autoAcceptInvitation: true,
    })

    this.agent.config.logger.debug('ConnectionController.receiveInvitation: connectionRecord.id: ', connectionRecord)

    if (!connectionRecord) {
      throw new CredoError('Processing invitation did not result in a connection record')
    }

    return this.mapConnection(connectionRecord)
  }

  @Post('/accept-invitation')
  async acceptInvitation(@BodyParams('id') id: string) {
    const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, id)

    return this.mapConnection(connection)
  }

  @Post('/accept-request')
  async acceptRequest(@BodyParams('id') id: string) {
    // possible here that the request hasn't finished processing yet
    await this.waitForState(id, DidExchangeState.RequestReceived)

    const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, id)

    return this.mapConnection(connection)
  }

  @Post('/send-ping')
  async sendPing(
    @BodyParams('id') id: string,
    // For now we ignore data. This could contain a comment property,
    // AFJ doesn't support passing it for now
    @BodyParams('data') data: any
  ) {
    const connection = await ConnectionUtils.getConnectionByConnectionIdOrOutOfBandId(this.agent, id)

    if (!connection) throw new NotFound(`Connection with id ${id} not found`)

    return this.mapConnection(connection)
  }

  private async mediatorIdFromMediatorConnectionId(mediatorConnectionId?: string): Promise<string | undefined> {
    if (!mediatorConnectionId) return undefined

    // Find mediator id if mediator connection id is provided
    const mediator = await this.agent.mediationRecipient.findByConnectionId(mediatorConnectionId)

    return mediator?.id
  }

  private async waitForState(id: string, state: DidExchangeState) {
    return await firstValueFrom(
      this.subject.pipe(
        filter((c) => c.payload.connectionRecord.id === id || c.payload.connectionRecord.outOfBandId === id),
        filter((c) => c.payload.connectionRecord.state === state),
        timeout(20000)
      )
    )
  }

  private mapConnection(connection: ConnectionRecord) {
    return {
      // If we use auto accept, we can't include the state as we will move quicker than the calls in the test harness. This will
      // make verification fail. The test harness recognizes the 'N/A' state.
      state: connection.state === DidExchangeState.Completed ? connection.rfc0160State : 'N/A',
      connection_id: connection.id,
      connection,
    }
  }
}
