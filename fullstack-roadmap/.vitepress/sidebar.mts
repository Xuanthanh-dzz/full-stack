import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const srcDir = path.resolve(fileURLToPath(new URL('.', import.meta.url)), '..')

/** Tên hiển thị của từng module, khớp bảng "Cây thư mục" trong README. */
const moduleTitles: Record<string, string> = {
  '00-huong-dan': 'Hướng dẫn & roadmap',
  '01-nen-tang-lap-trinh': 'Nền tảng lập trình với C',
  '02-c-chuyen-sau': 'C chuyên sâu: pointer & bộ nhớ',
  '03-cpp': 'C++20: OOP, STL và RAII',
  '04-csharp-co-ban': 'C# cơ bản',
  '05-csharp-nang-cao': 'C# nâng cao',
  '06-oop-va-thiet-ke': 'OOP và thiết kế',
  '07-cau-truc-du-lieu-giai-thuat': 'Cấu trúc dữ liệu & giải thuật',
  '08-sql-va-csdl': 'SQL và cơ sở dữ liệu',
  '09-linq-va-ef-core': 'LINQ và EF Core',
  '10-web-nen-tang': 'Nền tảng web',
  '11-aspnet-core-backend': 'Backend ASP.NET Core',
  '12-frontend': 'Frontend',
  '13-fullstack-tich-hop': 'Full-stack tích hợp',
  '14-testing-chat-luong': 'Testing và chất lượng',
  '15-devops-trien-khai': 'DevOps và triển khai',
  '16-design-pattern': 'Design pattern',
  '17-kien-truc-phan-mem': 'Kiến trúc phần mềm',
  '18-thiet-ke-he-thong': 'Thiết kế hệ thống',
  '19-cong-nghe-hien-dai': 'Công nghệ hiện đại',
  '20-ky-nang-architect': 'Kỹ năng architect',
  '21-du-an-thuc-hanh': 'Dự án thực hành'
}

/** Lấy `# Tiêu đề` đầu tiên của file làm nhãn sidebar; bỏ backtick để không lộ ký tự markdown. */
function readTitle(file: string, fallback: string): string {
  const heading = fs
    .readFileSync(file, 'utf8')
    .split(/\r?\n/)
    .find((line) => line.startsWith('# '))

  return heading ? heading.slice(2).replace(/`/g, '').trim() : fallback
}

export function buildSidebar() {
  const modules = fs
    .readdirSync(srcDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && /^\d{2}-/.test(entry.name))
    .map((entry) => entry.name)
    .sort()

  const groups = modules.map((dir) => {
    const items = fs
      .readdirSync(path.join(srcDir, dir))
      .filter((name) => name.endsWith('.md'))
      .sort()
      .map((name) => ({
        text: readTitle(path.join(srcDir, dir, name), name),
        link: `/${dir}/${name.replace(/\.md$/, '')}`
      }))

    return {
      text: `${dir.slice(0, 2)}. ${moduleTitles[dir] ?? dir.slice(3)}`,
      collapsed: true,
      items
    }
  })

  return [
    {
      text: 'Bắt đầu',
      items: [
        { text: 'Giới thiệu bộ tài liệu', link: '/gioi-thieu' },
        { text: 'Tiến độ biên soạn', link: '/PROGRESS' }
      ]
    },
    ...groups
  ]
}
