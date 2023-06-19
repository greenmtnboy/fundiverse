

class AuthRedirectException extends Error {
    constructor(message) {
        super(message);
        this.name = 'AuthRedirectException';
    }
}

const exceptions = {
    'auth': AuthRedirectException
}

export default exceptions;