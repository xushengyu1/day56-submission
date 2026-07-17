export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fieldErrors?: Record<string, string>,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

export function toApiError(error: unknown): ApiError {
  const response = typeof error === 'object' && error !== null && 'response' in error
    ? (error as { response?: { status?: number; data?: unknown } }).response
    : undefined
  const body = response?.data
  const payload = typeof body === 'object' && body !== null ? body as Record<string, unknown> : {}
  const status = response?.status ?? 0
  const code = typeof payload.error_code === 'string' ? payload.error_code : `HTTP_${status || 'NETWORK'}`
  const message = typeof payload.message === 'string' ? payload.message : '请求失败，请稍后重试'
  const fieldErrors = typeof payload.field_errors === 'object' && payload.field_errors !== null
    ? payload.field_errors as Record<string, string>
    : undefined
  return new ApiError(status, code, message, fieldErrors)
}
