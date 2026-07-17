import { Link } from 'react-router-dom'

export function ClaimProgressPage() {
  const steps = [
    { label: '提交申请', status: 'done' },
    { label: '核验通过', status: 'done' },
    { label: '待交接', status: 'current' },
    { label: '已认领', status: 'pending' },
  ]

  return (
    <div className="flex h-full">
      {/* 左侧：物品信息 */}
      <div className="w-[400px] bg-white border-r border-gray-100 p-6 flex-shrink-0">
        <h3 className="text-sm font-semibold text-gray-500 mb-4">认领物品</h3>
        <div className="w-full h-48 bg-gray-100 rounded-xl overflow-hidden mb-4">
          <img src="https://images.unsplash.com/photo-1556306535-0f09a537f0a3?w=400&h=192&fit=crop" alt="物品图片" className="w-full h-full object-cover" />
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-lg font-bold text-gray-900">黑色折叠伞</p>
            <div className="flex gap-2 mt-1">
              <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">其他物品</span>
              <span className="px-2 py-0.5 bg-emerald-50 text-emerald-600 text-xs rounded-full">高匹配</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600"><i className="fas fa-clock text-gray-400 w-4"></i><span>招领时间：7 月 16 日 上午 10:30</span></div>
          <div className="flex items-center gap-2 text-sm text-gray-600"><i className="fas fa-location-dot text-gray-400 w-4"></i><span>招领地点：教学楼 B 区 2 楼</span></div>
        </div>
        <div className="mt-6 p-4 bg-gray-50 rounded-xl">
          <p className="text-xs text-gray-400 mb-2">申请信息</p>
          <div className="space-y-2">
            <div className="flex justify-between text-sm"><span className="text-gray-500">申请时间</span><span className="text-gray-900 font-medium">7月16日 14:30</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500">核验方式</span><span className="text-gray-900 font-medium">隐藏特征核验</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500">申请编号</span><span className="text-gray-900 font-mono text-xs">CLM-20260716-001</span></div>
          </div>
        </div>
      </div>

      {/* 右侧：状态详情 */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center">
              <i className="fas fa-handshake text-emerald-600 text-3xl"></i>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">待交接</h2>
              <p className="text-gray-500 mt-1">核验通过，请与拾得者线下交接</p>
            </div>
          </div>

          {/* 进度条 */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
            <div className="flex items-center justify-between">
              {steps.map((step, i) => (
                <div key={step.label} className="flex items-center flex-1">
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      step.status === 'done' ? 'bg-emerald-500 text-white' :
                      step.status === 'current' ? 'bg-blue-600 text-white' :
                      'bg-gray-200 text-gray-400'
                    }`}>
                      {step.status === 'done' ? <i className="fas fa-check"></i> : <i className={`fas ${step.status === 'current' ? 'fa-handshake' : 'fa-flag-checkered'}`}></i>}
                    </div>
                    <span className={`text-xs mt-2 font-medium ${
                      step.status === 'done' ? 'text-emerald-600' : step.status === 'current' ? 'text-blue-600' : 'text-gray-400'
                    }`}>{step.label}</span>
                  </div>
                  {i < steps.length - 1 && <div className={`flex-1 h-1 mx-2 ${step.status === 'done' ? 'bg-emerald-300' : 'bg-gray-200'}`}></div>}
                </div>
              ))}
            </div>
          </div>

          {/* 联系方式卡片 */}
          <div className="bg-white rounded-2xl border-2 border-emerald-200 p-6 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center"><i className="fas fa-address-card text-emerald-600"></i></div>
              <div>
                <h3 className="text-base font-bold text-gray-900">拾得者联系方式</h3>
                <p className="text-xs text-gray-500">请联系拾得者约定交接时间和地点</p>
              </div>
            </div>
            <div className="space-y-3 p-4 bg-emerald-50 rounded-xl">
              <div className="flex items-center gap-3"><i className="fas fa-user text-emerald-500 w-5"></i><span className="text-sm font-medium text-gray-900">李同学</span></div>
              <div className="flex items-center gap-3"><i className="fas fa-phone text-emerald-500 w-5"></i><span className="text-sm font-medium text-gray-900">138****6789</span></div>
              <div className="flex items-center gap-3"><i className="fas fa-envelope text-emerald-500 w-5"></i><span className="text-sm font-medium text-gray-900">li***@campus.edu.cn</span></div>
            </div>
          </div>

          {/* 核验摘要 */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
            <h3 className="text-base font-bold text-gray-900 mb-4">核验摘要</h3>
            <div className="space-y-3">
              {['准确描述了伞套内侧标记', '正确描述了把手修复痕迹', '准确描述了伞面细节'].map((text, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-emerald-50 rounded-lg">
                  <div className="w-6 h-6 bg-emerald-100 rounded-full flex items-center justify-center"><i className="fas fa-check text-emerald-600 text-xs"></i></div>
                  <p className="text-sm text-emerald-800">问题 {i + 1}：匹配 — {text}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 bg-blue-50 rounded-lg flex items-center gap-2">
              <i className="fas fa-robot text-blue-500"></i>
              <p className="text-xs text-blue-700">AI 判定：全部关键回答匹配，置信度 0.94，自动进入待交接</p>
            </div>
          </div>

          <div className="p-4 bg-amber-50 rounded-xl">
            <div className="flex items-start gap-3">
              <i className="fas fa-info-circle text-amber-500 mt-0.5"></i>
              <div>
                <p className="text-sm font-medium text-amber-800">交接说明</p>
                <p className="text-xs text-amber-700 mt-1 leading-relaxed">请与拾得者约定安全的公共场所进行交接。交接完成后，由拾得者在系统中标记"已认领"。</p>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <Link to="/" className="inline-flex items-center gap-2 px-6 py-3 border-2 border-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-50">
              <i className="fas fa-arrow-left"></i>返回首页
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
