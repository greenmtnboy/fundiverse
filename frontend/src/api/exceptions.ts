

class AuthRedirectException extends Error {
    constructor(message) {
        super(message);
        this.name = 'AuthRedirectException';
    }
}

class AuthExtraRequiredException extends Error {
    constructor(message) {
        super(message);
        this.name = 'AuthExtraRequiredException';
    }
}

const exceptions = {
    'auth': AuthRedirectException,
    'auth_extra': AuthExtraRequiredException
}

export default exceptions;