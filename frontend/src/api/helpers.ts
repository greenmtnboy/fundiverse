import { isFetchError } from "./instance";

const apiHelpers = {
  getErrorMessage(error: Error): string {
    let base = error.message || "An error occured.";
    if (isFetchError(error) && error.response?.data?.detail) {
      base = error.response.data.detail;
    }
    return base;
  },
  getResultCode(error: Error): number {
    let base = 400;
    if (isFetchError(error)) {
      if (error.response?.data) {
        base = error.response.status;
      }
    }
    return base;
  },
};

export default apiHelpers;
