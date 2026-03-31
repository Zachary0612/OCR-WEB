<template>
  <div class="min-h-screen bg-gray-50">
    <header class="border-b border-gray-200 bg-white shadow-sm">
      <div class="mx-auto flex max-w-full items-center justify-between px-6 py-3">
        <div class="flex items-center space-x-3">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </div>
          <div>
            <h1 class="text-lg font-bold text-gray-800">PaddleOCR 文档识别系统</h1>
            <p class="text-xs text-gray-400">文档上传、识别、检索与结果整理</p>
          </div>
        </div>

        <nav class="flex items-center space-x-1">
          <router-link
            to="/"
            class="rounded-md px-3 py-1.5 text-sm transition"
            :class="$route.path === '/' ? 'bg-blue-50 font-medium text-blue-700' : 'text-gray-600 hover:text-gray-800'"
          >
            工作台
          </router-link>
          <router-link
            to="/search"
            class="rounded-md px-3 py-1.5 text-sm transition"
            :class="$route.path === '/search' ? 'bg-blue-50 font-medium text-blue-700' : 'text-gray-600 hover:text-gray-800'"
          >
            搜索
          </router-link>
        </nav>
      </div>
    </header>

    <router-view />
  </div>
</template>
