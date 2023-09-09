import axios from 'axios';
import store from '/src/store'
import exceptions from './exceptions';
import { ipcRenderer } from 'electron';

// must match port in backend\src\main.py
const instance = axios.create({
  baseURL: 'http://localhost:3042',
}
);




// Listen for the shared-variable event
if (ipcRenderer) {
  ipcRenderer.on('api-key', (_, API_KEY) => {
    // Now you can use the sharedVariable in your renderer process
    console.log(API_KEY);
    instance.defaults.headers.post['Authorization'] = `Bearer ${API_KEY}`;
    instance.defaults.headers.get['Authorization'] = `Bearer ${API_KEY}`;
  });
}



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
