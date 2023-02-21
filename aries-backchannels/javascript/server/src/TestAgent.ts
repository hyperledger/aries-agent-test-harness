import { $log } from '@tsed/common'
import { Agent, AutoAcceptCredential, AutoAcceptProof, CredentialsModule, DidsModule, InitConfig, ProofsModule, V2CredentialProtocol, V2ProofProtocol } from '@aries-framework/core'
import { agentDependencies } from '@aries-framework/node'
import { AskarModule } from '@aries-framework/askar'
import { AnonCredsModule, LegacyIndyCredentialFormatService, LegacyIndyProofFormatService,  V1CredentialProtocol, V1ProofProtocol } from '@aries-framework/anoncreds'
import { AnonCredsRsModule } from '@aries-framework/anoncreds-rs'
import { IndyVdrAnonCredsRegistry, IndyVdrModule, IndyVdrSovDidResolver } from '@aries-framework/indy-vdr'
import { TsedLogger } from './TsedLogger'
import { TransportConfig } from './TestHarnessConfig'
import { IndyVdrPoolConfig } from '@aries-framework/indy-vdr/build/pool'

export async function createAgent({
  publicDidSeed,
  genesisPath,
  agentName,
  transport,
}: {
  publicDidSeed: string
  genesisPath: string
  agentName: string
  transport: TransportConfig
}) {
  // TODO: Public did does not seem to be registered
  // TODO: Schema is prob already registered

  const agentConfig: InitConfig = {
    label: agentName,
    walletConfig: {
      id: `aath-javascript-${Date.now()}`,
      key: '00000000000000000000000000000Test01',
    },
    endpoints: transport.endpoints,
    publicDidSeed,
    // Needed to accept mediation requests: https://github.com/hyperledger/aries-framework-javascript/issues/668
    autoAcceptMediationRequests: true,
    useDidSovPrefixWhereAllowed: true,
    logger: new TsedLogger($log),
  }

  const genesisTransactions = await new agentDependencies.FileSystem().read(genesisPath)

  const agent = new Agent({ config: agentConfig, dependencies: agentDependencies,
    modules: getAskarAnonCredsIndyModules({
      indyNamespace: 'main-pool',
      isProduction: false,
      genesisTransactions,
    }),
  })

  // If at least a link secret is found, we assume there is a default one
  if ((await agent.modules.anoncreds.getLinkSecretIds()).length === 0) {
    await agent.modules.anoncreds.createLinkSecret()
  }

  for (const it of transport.inboundTransports) {
    agent.registerInboundTransport(it)
  }

  for (const ot of transport.outboundTransports) {
    agent.registerOutboundTransport(ot)
  }

  await agent.initialize()

  return agent
}

export function getAskarAnonCredsIndyModules(indyNetworkConfig: IndyVdrPoolConfig) {
  const legacyIndyCredentialFormatService = new LegacyIndyCredentialFormatService()
  const legacyIndyProofFormatService = new LegacyIndyProofFormatService()

  return {
    credentials: new CredentialsModule({
      autoAcceptCredentials: AutoAcceptCredential.ContentApproved,
      credentialProtocols: [
        new V1CredentialProtocol({
          indyCredentialFormat: legacyIndyCredentialFormatService,
        }),
        new V2CredentialProtocol({
          credentialFormats: [legacyIndyCredentialFormatService],
        }),
      ],
    }),
    proofs: new ProofsModule({
      autoAcceptProofs: AutoAcceptProof.ContentApproved,
      proofProtocols: [
        new V1ProofProtocol({
          indyProofFormat: legacyIndyProofFormatService,
        }),
        new V2ProofProtocol({
          proofFormats: [legacyIndyProofFormatService],
        }),
      ],
    }),
    anoncreds: new AnonCredsModule({
      registries: [new IndyVdrAnonCredsRegistry()],
    }),
    anoncredsRs: new AnonCredsRsModule(),
    indyVdr: new IndyVdrModule({
      networks: [indyNetworkConfig],
    }),
    dids: new DidsModule({
      resolvers: [new IndyVdrSovDidResolver()],
    }),
    askar: new AskarModule(),
  } as const
}
