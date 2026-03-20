export interface PasswordCheck {
  label: string;
  test: (pw: string) => boolean;
}

export const PASSWORD_CHECKS: PasswordCheck[] = [
  { label: "At least 8 characters", test: (pw) => pw.length >= 8 },
  { label: "One uppercase letter", test: (pw) => /[A-Z]/.test(pw) },
  { label: "One lowercase letter", test: (pw) => /[a-z]/.test(pw) },
  { label: "One number", test: (pw) => /\d/.test(pw) },
  { label: "One special character", test: (pw) => /[^A-Za-z0-9]/.test(pw) },
];

export function isPasswordStrong(password: string): boolean {
  return PASSWORD_CHECKS.every((check) => check.test(password));
}
