import { WebPlugin } from "@capacitor/core";
import type { EchoPlugin } from "./definitions";

export class EchoWeb extends WebPlugin implements EchoPlugin {
  constructor() {
    super();
    console.log("🔌 Web: EchoWeb plugin initialized");
  }

  echo(options: { value: string }): Promise<{ value: string }> {
    console.log("🔌 Web: echo method called with:", options);
    console.log("🔌 Web: returning value:", options.value);
    return Promise.resolve({ value: options.value });
  }
}
