import axios from 'axios';
import store from '/src/store'
import exceptions from './exceptions';

// must match port in backend\src\main.py
const instance = axios.create({
  baseURL: 'http://localhost:3042',
}
);

instance.defaults.headers.common['Authorization'] = AUTH_TOKEN;

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
        store.getters.providers.forEach((provider: string) => {
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
