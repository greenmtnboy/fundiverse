import axios from 'axios';
import store from '@/store'
import exceptions from './exceptions';


const instance = axios.create({
  baseURL: 'http://localhost:3000',
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

      // Redirect based on the error code
      if (status === 401) {
        console.log('NEED TO USE STORE')
        store.getters.providers.forEach((provider: string) => {
          console.log('checking if logged in for')
          console.log(provider)
          store.dispatch('probeLogin', { provider: provider })
        })
        return Promise.reject(new exceptions.auth('User is not authenticated'))
      }
      else if (status === 412) {
        return Promise.reject(new exceptions.auth_extra('Extra authentication factor required'))
      }

      // Add more conditions for other error codes as needed
    }

    // Return the error to propagate it further
    return Promise.reject(error);
  }
);

export default instance;
