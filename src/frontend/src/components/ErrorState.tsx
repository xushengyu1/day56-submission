import ReloadOutlined from '@ant-design/icons/ReloadOutlined'
import WarningOutlined from '@ant-design/icons/WarningOutlined'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function ErrorState({ title = '加载失败', message = '请稍后重试', onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16">
      <WarningOutlined aria-hidden="true" className="text-4xl text-red-400 mb-4" />
      <h3 className="text-lg font-bold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500 mb-4">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-xl hover:bg-blue-700">
          <ReloadOutlined aria-hidden="true" className="mr-1" />重试
        </button>
      )}
    </div>
  )
}
