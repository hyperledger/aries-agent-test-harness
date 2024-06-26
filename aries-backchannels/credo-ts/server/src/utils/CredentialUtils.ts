import { Agent, CredentialRepository } from '@credo-ts/core'
import { AnonCredsCredentialInfo, AnonCredsCredentialRepository, AnonCredsHolderService, AnonCredsHolderServiceSymbol } from '@credo-ts/anoncreds'

export class CredentialUtils {
  public static async getCredentialByThreadId(agent: Agent, threadId: string) {
    const credentialRepository = agent.dependencyManager.resolve(CredentialRepository)
    return credentialRepository.getSingleByQuery(agent.context, { threadId })
  }

  public static async getAnonCredsCredentialById(agent: Agent, credentialId: string): Promise<Record<string, unknown>> {
    const holderService = agent.dependencyManager.resolve<AnonCredsHolderService>(AnonCredsHolderServiceSymbol)
    const credentialInfo = await holderService.getCredential(agent.context, { credentialId })

    return {
      attrs: credentialInfo.attributes,
      cred_def_id: credentialInfo.credentialDefinitionId,
      referent: credentialInfo.credentialId,
      schema_id: credentialInfo.schemaId,
      cred_rev_id: credentialInfo.credentialRevocationId,
      rev_reg_id: credentialInfo.revocationRegistryId,
    }
  }
}
