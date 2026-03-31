import { isFetchError } from "./instance";

const axiosHelpers = {
  getErrorMessage(error: Error): string {
    let base = "An error occured.";
    if (isFetchError(error)) {
      base = error.message;
      if (error.response?.data) {
        base = error.response.data.detail;
      }
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

export default axiosHelpers;
