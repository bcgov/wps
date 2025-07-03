export interface EchoPlugin {
  echo(options: { value: string }): Promise<{ value: string }>;
}
