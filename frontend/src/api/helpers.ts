import axios from "axios";

const axiosHelpers = {
  getErrorMessage(error: Error): string {
    let base = "An error occured.";
    if (axios.isAxiosError(error)) {
      base = error.message;
      if (error.response && error.response.data) {
        base = error.response.data.detail;
      }
    }
    return base;
  },
  getResultCode(error: Error): number {
    let base = 400;
    if (axios.isAxiosError(error)) {
      if (error.response && error.response.data) {
        base = error.response.status;
      }
    }
    return base;
  },
};

export default axiosHelpers;
