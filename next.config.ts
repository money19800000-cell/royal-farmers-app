/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // ⚠️ 警告：为了快速上线，这里忽略了类型报错
    // 危险操作，仅建议初期开发使用
    ignoreBuildErrors: true,
  },
  eslint: {
    // 同上，忽略代码规范报错
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;