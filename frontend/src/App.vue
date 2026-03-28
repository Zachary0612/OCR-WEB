<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-full mx-auto px-6 py-3 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </div>
          <h1 class="text-lg font-bold text-gray-800">PaddleOCR 文档识别系统</h1>
          <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">v2.0</span>
        </div>
        <nav class="flex items-center space-x-1">
          <router-link to="/" class="px-3 py-1.5 text-sm rounded-md transition"
            :class="$route.path === '/' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:text-gray-800'">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>工作台
          </router-link>
          <router-link to="/search" class="px-3 py-1.5 text-sm rounded-md transition"
            :class="$route.path === '/search' ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-600 hover:text-gray-800'">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>搜索
          </router-link>
        </nav>
      </div>
    </header>
    <router-view />
  </div>
</template>
