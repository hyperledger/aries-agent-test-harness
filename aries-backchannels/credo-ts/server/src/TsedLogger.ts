import { Logger } from '@tsed/common'
import { LogLevel, BaseLogger } from '@credo-ts/core'
import util from 'util'

export class TsedLogger extends BaseLogger {
  private logger: Logger

  // Map our log levels to tslog levels
  private tsedLogLevelMap = {
    [LogLevel.test]: 'debug',
    [LogLevel.trace]: 'debug',
    [LogLevel.debug]: 'debug',
    [LogLevel.info]: 'info',
    [LogLevel.warn]: 'warn',
    [LogLevel.error]: 'error',
    [LogLevel.fatal]: 'fatal',
  } as const

  public constructor(logger: Logger) {
    super(LogLevel.debug)
    this.logger = logger
  }

  private log(level: Exclude<LogLevel, LogLevel.off>, message: string, data?: Record<string, any>): void {
    const tsedLogLevel = this.tsedLogLevelMap[level]

    if (data) {
      this.logger[tsedLogLevel](message, util.inspect(data, { showHidden: false, depth: null }))
    } else {
      this.logger[tsedLogLevel](message)
    }
  }

  public test(message: string, data?: Record<string, any>): void {
    this.log(LogLevel.test, message, data)
  }

  public trace(message: string, data?: Record<string, any>): void {
    this.log(LogLevel.trace, message, data)
  }

  public debug(message: string, data?: Record<string, any>): void {
    this.log(LogLevel.debug, message, data)
  }

  public info(message: string, data?: Record<string, any>): void {
    this.log(LogLevel.info, message, data)
  }

  public warn(message: string, data?: Record<string, any>): void {
    this.log(LogLevel.warn, message, data)
  }

  public error(message: string, data?: Record<string, any>): void {
    this.log(LogLevel.error, message, data)
  }

  public fatal(message: string, data?: Record<string, any>): void {
    this.log(LogLevel.fatal, message, data)
  }
}
