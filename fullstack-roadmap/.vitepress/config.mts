import { defineConfig } from 'vitepress'
import taskLists from 'markdown-it-task-lists'
import { buildSidebar } from './sidebar.mts'

// GitHub Pages phục vụ site tại https://<user>.github.io/full-stack/ nên cần base khớp tên repo.
const base = process.env.DOCS_BASE ?? '/full-stack/'

export default defineConfig({
  base,
  lang: 'vi-VN',
  title: 'Full-stack Roadmap',
  description:
    'Bộ tài liệu tự học tiếng Việt: C, C++20, C#/.NET 9, SQL, web, kiến trúc phần mềm và thiết kế hệ thống.',
  cleanUrls: true,
  lastUpdated: true,

  // PROMPT.md là tài liệu nội bộ để biên soạn, không thuộc nội dung học.
  srcExclude: ['PROMPT.md'],

  // README.md mặc định chiếm route `/`; đẩy nó sang `/gioi-thieu` để index.md làm trang chủ.
  rewrites: { 'README.md': 'gioi-thieu.md' },

  head: [['meta', { name: 'theme-color', content: '#3c8772' }]],

  markdown: {
    lineNumbers: true,
    // Bài học dùng ## cho phần chính và ### cho mục con.
    toc: { level: [2, 3] },
    // PROGRESS.md theo dõi tiến độ bằng `- [x]` / `- [ ]`; render thành checkbox thật.
    config: (md) => {
      md.use(taskLists, { enabled: false, label: true })
    }
  },

  themeConfig: {
    outline: { level: [2, 3], label: 'Nội dung bài' },

    nav: [
      { text: 'Giới thiệu', link: '/gioi-thieu' },
      { text: 'Roadmap', link: '/00-huong-dan/roadmap' },
      { text: 'Tiến độ', link: '/PROGRESS' },
      { text: 'Bắt đầu học', link: '/01-nen-tang-lap-trinh/01-bai-toan-thuat-toan-va-pseudocode' }
    ],

    sidebar: buildSidebar(),

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Xuanthanh-dzz/full-stack' }
    ],

    editLink: {
      pattern:
        'https://github.com/Xuanthanh-dzz/full-stack/edit/main/fullstack-roadmap/:path',
      text: 'Sửa trang này trên GitHub'
    },

    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: 'Tìm kiếm', buttonAriaLabel: 'Tìm kiếm' },
          modal: {
            displayDetails: 'Hiện chi tiết',
            resetButtonTitle: 'Xóa từ khóa',
            backButtonTitle: 'Quay lại',
            noResultsText: 'Không tìm thấy kết quả cho',
            footer: {
              selectText: 'chọn',
              navigateText: 'di chuyển',
              closeText: 'đóng'
            }
          }
        }
      }
    },

    docFooter: { prev: 'Bài trước', next: 'Bài tiếp theo' },
    darkModeSwitchLabel: 'Giao diện',
    lightModeSwitchTitle: 'Chuyển sang giao diện sáng',
    darkModeSwitchTitle: 'Chuyển sang giao diện tối',
    sidebarMenuLabel: 'Mục lục',
    returnToTopLabel: 'Lên đầu trang',
    lastUpdated: { text: 'Cập nhật lần cuối' },

    footer: {
      message: 'Bộ tài liệu tự học full-stack bằng tiếng Việt.',
      copyright: 'Nội dung theo repo Xuanthanh-dzz/full-stack'
    }
  }
})
