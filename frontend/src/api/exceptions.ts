class AuthRedirectException extends Error {
  constructor(message) {
    super(message);
    this.name = "ProviderAuthenticationError";
  }
}

class AuthExtraRequiredException extends Error {
  constructor(message) {
    super(message);
    this.name = "AuthExtraRequiredException";
  }
}
class AuthExternalLoginRequiredException extends Error {
  constructor(message) {
    super(message);
    this.name = "AuthExternalLoginRequiredException";
  }
}
const exceptions = {
  auth: AuthRedirectException,
  auth_extra: AuthExtraRequiredException,
  auth_external_login: AuthExternalLoginRequiredException,
};

export default exceptions;
