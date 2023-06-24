import axios from 'axios';
import router from '../router';
import exceptions from './exceptions';

const instance = axios.create();


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
          // Redirect to a specific URL for 401 error
          router.push({
            name: 'login'
        })
        return Promise.reject(new exceptions.auth('User is not authenticated'))
        } 
        // Add more conditions for other error codes as needed
      }
  
      // Return the error to propagate it further
      return Promise.reject(error);
    }
  );

  export default instance;
