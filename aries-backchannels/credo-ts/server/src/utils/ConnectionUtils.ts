import { Agent, ConnectionRecord } from '@credo-ts/core'
import { NotFound } from '@tsed/exceptions'

export class ConnectionUtils {
  /**
   * The connection id is not available yet when creating a connection invitation. Instead, we return the out of band id
   * and use this method to find the associated connection for a given out of band id.
   */
  public static async getConnectionByConnectionIdOrOutOfBandId(agent: Agent, id: string): Promise<ConnectionRecord> {
    const connection = await agent.connections.findById(id)

    if (connection) return connection

    const connections = await agent.connections.findAllByOutOfBandId(id)

    if (connections.length === 0) throw new NotFound(`Connection with id ${id} not found`)

    return connections[0]
  }
}
