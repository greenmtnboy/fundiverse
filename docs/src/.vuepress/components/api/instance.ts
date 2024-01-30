import axios from 'axios';
// import exceptions from './exceptions';

export const instance = axios.create({
  baseURL: 'http://localhost:5000',
}
);

instance.interceptors.response.use(
  response => {
    // If the response is successful, pass it through
    return response;
  },
  error => {
    if (error.response) {
      // Access the HTTP status code
      const status = error.response.status;

      // Add more conditions for other error codes as needed
    }

    // Return the error to propagate it further
    return Promise.reject(error);
  }
);

const desiredResponseCode = 200;

const maxAsyncMinutes = 10;

// Define a function for making the Axios request
async function makeAsyncRequestInner(guid, startTime) {
  const currentTime = Date.now();
  if (currentTime - startTime >= maxAsyncMinutes * 60 * 1000) {
    console.log("Loop has been running for more than 5 minutes. Breaking the loop.");
    return; // Exit the loop
  }
  try {
    const response = await instance.get(`background_tasks/${guid}`);
    const { status } = response;
    if (status === desiredResponseCode) {
      return response
    } else {
      await new Promise(resolve => setTimeout(resolve, 500));
      return await makeAsyncRequestInner(guid, startTime);
    }
  } catch (error) {
    throw error;
  }
}

export async function makeAsyncRequest(asyncApi, args) {
  const response = await instance.post(`async_${asyncApi}`, args);
  const guid = response.data.guid;
  const startTime = Date.now();
  return await makeAsyncRequestInner(guid, startTime)
}


// Start the polling loop
instance['makeAsyncRequest'] = makeAsyncRequest


