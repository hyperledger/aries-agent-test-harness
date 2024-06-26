import { $log, Logger, registerProvider } from '@tsed/common'
import minimist from 'minimist'

import { TestHarnessConfig } from './TestHarnessConfig'
import { PlatformExpress } from '@tsed/platform-express'
import { Server } from './Server'

async function startup() {
  const cliArguments = minimist(process.argv.slice(2), {
    alias: {
      port: 'p',
    },
    default: {
      port: 9020,
    },
  })

  const testHarnessConfig = new TestHarnessConfig({ backchannelPort: Number(cliArguments.port) })

  registerProvider({
    provide: TestHarnessConfig,
    useValue: testHarnessConfig,
  })

  $log.level = 'debug'

  // TODO: Set up native logger for anoncreds, askar and indy-vdr

  await testHarnessConfig.startAgent({ inboundTransports: ['http'], outboundTransports: ['http'] })

  try {
    $log.debug('Start server...')
    const platform = await PlatformExpress.bootstrap(Server)

    platform.settings.port = testHarnessConfig.backchannelPort

    await testHarnessConfig.agentStartup()

    await platform.listen()

    $log.level = 'debug'
  } catch (er) {
    $log.error(er)

    throw er
  }
}

startup()
