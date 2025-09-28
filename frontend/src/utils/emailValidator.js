/**
 * Shared Email Validation Utility (Frontend)
 * Robust email validation supporting plus-addressing, subdomains, hyphens, and modern TLDs
 * Matches backend validation logic exactly
 */

export class EmailValidator {
  // Comprehensive email regex pattern
  // Supports: user+tag@sub.domain.tld, user_name-1@domain.io, user'test@domain.com etc.
  static EMAIL_PATTERN = /^[a-zA-Z0-9._%+'-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  /**
   * Validate email address with comprehensive rules
   * @param {string} email - Email address to validate
   * @returns {boolean} True if email is valid, false otherwise
   */
  static isValidEmail(email) {
    if (!email || typeof email !== 'string') {
      return false;
    }

    // Basic format check
    if (!EmailValidator.EMAIL_PATTERN.test(email)) {
      return false;
    }

    // Additional checks
    return EmailValidator._additionalChecks(email);
  }

  /**
   * Validate email with detailed error message
   * @param {string} email - Email address to validate
   * @returns {[boolean, string]} [isValid, errorMessage]
   */
  static validateEmailDetailed(email) {
    if (!email || typeof email !== 'string') {
      return [false, 'Email is required'];
    }

    email = email.trim();

    if (!email) {
      return [false, 'Email cannot be empty'];
    }

    if (email.length > 254) { // RFC 5321 limit
      return [false, 'Email address is too long (max 254 characters)'];
    }

    const atCount = (email.match(/@/g) || []).length;
    if (atCount !== 1) {
      return [false, 'Email must contain exactly one @ symbol'];
    }

    const [localPart, domainPart] = email.split('@');

    // Validate local part (before @)
    const [localValid, localError] = EmailValidator._validateLocalPart(localPart);
    if (!localValid) {
      return [false, localError];
    }

    // Validate domain part (after @)
    const [domainValid, domainError] = EmailValidator._validateDomainPart(domainPart);
    if (!domainValid) {
      return [false, domainError];
    }

    return [true, ''];
  }

  /**
   * Additional validation checks
   * @private
   */
  static _additionalChecks(email) {
    // Check for consecutive dots
    if (email.includes('..')) {
      return false;
    }

    // Check for leading/trailing dots in local part
    const localPart = email.split('@')[0];
    if (localPart.startsWith('.') || localPart.endsWith('.')) {
      return false;
    }

    // Check domain has valid TLD
    const domainPart = email.split('@')[1];
    if (!domainPart.includes('.')) {
      return false;
    }

    const parts = domainPart.split('.');
    const tld = parts[parts.length - 1];

    // TLD must be at least 2 characters and contain only letters
    if (tld.length < 2 || !/^[a-zA-Z]+$/.test(tld)) {
      return false;
    }

    return true;
  }

  /**
   * Validate the local part (before @) of email
   * @private
   */
  static _validateLocalPart(localPart) {
    if (!localPart) {
      return [false, 'Local part cannot be empty'];
    }

    if (localPart.length > 64) { // RFC 5321 limit
      return [false, 'Local part is too long (max 64 characters)'];
    }

    if (localPart.startsWith('.') || localPart.endsWith('.')) {
      return [false, 'Local part cannot start or end with a dot'];
    }

    if (localPart.includes('..')) {
      return [false, 'Local part cannot contain consecutive dots'];
    }

    // Check allowed characters
    const allowedChars = /^[a-zA-Z0-9!#$%&'*+-/=?^_`{|}~.]+$/;
    if (!allowedChars.test(localPart)) {
      return [false, 'Local part contains invalid characters'];
    }

    return [true, ''];
  }

  /**
   * Validate the domain part (after @) of email
   * @private
   */
  static _validateDomainPart(domainPart) {
    if (!domainPart) {
      return [false, 'Domain part cannot be empty'];
    }

    if (domainPart.length > 253) { // RFC 1035 limit
      return [false, 'Domain part is too long (max 253 characters)'];
    }

    if (domainPart.startsWith('.') || domainPart.endsWith('.')) {
      return [false, 'Domain cannot start or end with a dot'];
    }

    if (domainPart.startsWith('-') || domainPart.endsWith('-')) {
      return [false, 'Domain cannot start or end with a hyphen'];
    }

    // Split into labels
    const labels = domainPart.split('.');

    if (labels.length < 2) {
      return [false, 'Domain must have at least one dot (e.g., domain.com)'];
    }

    for (const label of labels) {
      const [labelValid, labelError] = EmailValidator._validateDomainLabel(label);
      if (!labelValid) {
        return [false, `Invalid domain label '${label}': ${labelError}`];
      }
    }

    // Check TLD (last label)
    const tld = labels[labels.length - 1];
    if (tld.length < 2) {
      return [false, 'Top-level domain must be at least 2 characters'];
    }

    if (!/^[a-zA-Z]+$/.test(tld)) {
      return [false, 'Top-level domain must contain only letters'];
    }

    return [true, ''];
  }

  /**
   * Validate a single domain label
   * @private
   */
  static _validateDomainLabel(label) {
    if (!label) {
      return [false, 'Domain label cannot be empty'];
    }

    if (label.length > 63) { // RFC 1035 limit
      return [false, 'Domain label is too long (max 63 characters)'];
    }

    if (label.startsWith('-') || label.endsWith('-')) {
      return [false, 'Domain label cannot start or end with hyphen'];
    }

    // Check allowed characters (letters, numbers, hyphens)
    if (!/^[a-zA-Z0-9-]+$/.test(label)) {
      return [false, 'Domain label contains invalid characters'];
    }

    return [true, ''];
  }

  /**
   * Normalize email address (lowercase, strip whitespace)
   * @param {string} email - Email address to normalize
   * @returns {string} Normalized email address
   */
  static normalizeEmail(email) {
    if (!email) {
      return '';
    }

    return email.trim().toLowerCase();
  }

  /**
   * Extract domain from email address
   * @param {string} email - Email address
   * @returns {string} Domain part or empty string if invalid
   */
  static extractDomain(email) {
    if (!email || !email.includes('@')) {
      return '';
    }

    return email.split('@')[1].toLowerCase();
  }

  /**
   * Check if email uses plus-addressing (e.g., user+tag@domain.com)
   * @param {string} email - Email address to check
   * @returns {boolean} True if email contains plus-addressing
   */
  static supportsPlusAddressing(email) {
    if (!email || !email.includes('@')) {
      return false;
    }

    const localPart = email.split('@')[0];
    return localPart.includes('+');
  }
}

// Convenience functions for easy imports
export const isValidEmail = (email) => EmailValidator.isValidEmail(email);
export const validateEmail = (email) => EmailValidator.validateEmailDetailed(email);
export const normalizeEmail = (email) => EmailValidator.normalizeEmail(email);

// Default export
export default EmailValidator;