export interface ErrorResult {
    status: number;
    message: string;
}

export class HttpError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  }