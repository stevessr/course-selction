<template>
  <div class="courses-management">
    <a-card>
      <template #title>
        <div class="card-title">
          <h2>课程管理 / Course Management</h2>
        </div>
      </template>

      <template #extra>
        <a-space>
          <a-button type="primary" @click="showBatchAssignModal" :disabled="selectedRowKeys.length === 0">
            <template #icon><UserAddOutlined /></template>
            分配教师
          </a-button>
          <a-button type="primary" @click="showImportModal">
            <template #icon><UploadOutlined /></template>
            批量导入
          </a-button>
          <a-button @click="exportCourses">
            <template #icon><DownloadOutlined /></template>
            导出课程
          </a-button>
          <a-button @click="loadCourses">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </a-space>
      </template>

      <!-- Search and Filter -->
      <div class="search-section">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索课程名称 / Search course name"
              @search="handleSearch"
              allow-clear
            >
              <template #prefix><SearchOutlined /></template>
            </a-input-search>
          </a-col>
          <a-col :span="6">
            <a-select
              v-model:value="filterCourseType"
              placeholder="课程类型 / Course Type"
              style="width: 100%"
              @change="handleSearch"
              allow-clear
            >
              <a-select-option value="required">必修 / Required</a-select-option>
              <a-select-option value="elective">选修 / Elective</a-select-option>
            </a-select>
          </a-col>
        </a-row>
      </div>

      <!-- Courses Table -->
      <a-table
        :columns="columns"
        :data-source="courses"
        :loading="loading"
        :pagination="pagination"
        :row-selection="rowSelection"
        @change="handleTableChange"
        row-key="course_id"
        class="courses-table"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'course_name'">
            <div>
              <div style="font-weight: 600;">{{ record.course_name }}</div>
              <div style="font-size: 12px; color: #888;">ID: {{ record.course_id }}</div>
            </div>
          </template>

          <template v-else-if="column.key === 'course_type'">
            <a-tag :color="record.course_type === 'required' ? 'red' : 'blue'">
              {{ record.course_type === 'required' ? '必修' : '选修' }}
            </a-tag>
          </template>

          <template v-else-if="column.key === 'capacity'">
            <a-progress
              :percent="Math.round((record.course_selected / record.course_capacity) * 100)"
              :status="record.course_selected >= record.course_capacity ? 'exception' : 'active'"
              size="small"
            />
            <div style="font-size: 12px; margin-top: 4px;">
              {{ record.course_selected }} / {{ record.course_capacity }}
            </div>
          </template>

          <template v-else-if="column.key === 'teacher'">
            <span v-if="record.teacher_name">{{ record.teacher_name }}</span>
            <span v-else style="color: #999;">未分配</span>
          </template>

          <template v-else-if="column.key === 'course_tags'">
            <a-tag v-for="tag in (record.course_tags || [])" :key="tag" color="green">
              {{ tag }}
            </a-tag>
            <span v-if="!record.course_tags || record.course_tags.length === 0" style="color: #999;">无标签</span>
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-tooltip title="编辑">
                <a-button size="small" @click="showEditModal(record)">
                  <template #icon><EditOutlined /></template>
                </a-button>
              </a-tooltip>

              <a-popconfirm
                title="确定要删除此课程吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="deleteCourse(record)"
              >
                <a-tooltip title="删除">
                  <a-button size="small" danger>
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-tooltip>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Edit Course Modal -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑课程 / Edit Course"
      @ok="handleUpdateCourse"
      @cancel="resetEditForm"
      :confirm-loading="editLoading"
      width="800px"
    >
      <a-form
        :model="editForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="课程名称 / Course Name">
          <a-input v-model:value="editForm.course_name" />
        </a-form-item>

        <a-form-item label="学分 / Credits">
          <a-input-number v-model:value="editForm.course_credit" :min="0" style="width: 100%" />
        </a-form-item>

        <a-form-item label="课程类型 / Type">
          <a-select v-model:value="editForm.course_type" style="width: 100%">
            <a-select-option value="required">必修 / Required</a-select-option>
            <a-select-option value="elective">选修 / Elective</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="地点 / Location">
          <a-input v-model:value="editForm.course_location" />
        </a-form-item>

        <a-form-item label="容量 / Capacity">
          <a-input-number v-model:value="editForm.course_capacity" :min="1" style="width: 100%" />
        </a-form-item>

        <a-form-item label="开始时间 / Time Begin">
          <a-input-number v-model:value="editForm.course_time_begin" style="width: 100%" />
        </a-form-item>

        <a-form-item label="结束时间 / Time End">
          <a-input-number v-model:value="editForm.course_time_end" style="width: 100%" />
        </a-form-item>

        <a-form-item label="课程标签 / Course Tags">
          <a-select 
            v-model:value="editForm.course_tags" 
            mode="tags" 
            placeholder="Enter tags"
            style="width: 100%"
          >
          </a-select>
        </a-form-item>

        <a-form-item label="备注 / Notes">
          <a-textarea v-model:value="editForm.course_notes" :rows="3" />
        </a-form-item>

        <a-form-item label="费用 / Cost">
          <a-input-number v-model:value="editForm.course_cost" :min="0" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Import Courses Modal -->
    <a-modal
      v-model:open="importModalVisible"
      title="批量导入课程 / Bulk Import Courses"
      @ok="handleImportCourses"
      @cancel="resetImportForm"
      :confirm-loading="importLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="上传 CSV 文件 / Upload CSV File">
          <a-upload-dragger
            v-model:fileList="importFileList"
            :before-upload="() => false"
            accept=".csv"
            :max-count="1"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 CSV 格式。请确保文件包含: course_name, course_credit, course_type, course_location, course_capacity, course_time_begin, course_time_end
            </p>
          </a-upload-dragger>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Batch Assign Teacher Modal -->
    <a-modal
      v-model:open="batchAssignModalVisible"
      title="批量分配教师 / Batch Assign Teacher"
      @ok="handleBatchAssignTeacher"
      @cancel="resetBatchAssignForm"
      :confirm-loading="batchAssignLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="选择教师 / Select Teacher">
          <a-select 
            v-model:value="selectedTeacherId" 
            placeholder="Select teacher"
            style="width: 100%"
            show-search
            :filter-option="filterTeacherOption"
          >
            <a-select-option v-for="teacher in teachers" :key="teacher.teacher_id" :value="teacher.teacher_id">
              {{ teacher.username }} (ID: {{ teacher.teacher_id }})
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-alert 
          type="info" 
          :message="`将为 ${selectedRowKeys.length} 门课程分配教师`"
          show-icon
        />
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import adminApi from '@/api/admin'
import {
  UploadOutlined,
  DownloadOutlined,
  ReloadOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  InboxOutlined,
  UserAddOutlined,
} from '@ant-design/icons-vue'

const authStore = useAuthStore()

// State
const loading = ref(false)
const courses = ref([])
const searchText = ref('')
const filterCourseType = ref(null)
const selectedRowKeys = ref([])

// Pagination
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 门课程`,
})

// Edit Modal
const editModalVisible = ref(false)
const editLoading = ref(false)
const editForm = reactive({
  course_id: null,
  course_name: '',
  course_credit: 0,
  course_type: 'required',
  course_location: '',
  course_capacity: 30,
  course_time_begin: 800,
  course_time_end: 950,
  course_tags: [],
  course_notes: '',
  course_cost: 0,
})

// Import Modal
const importModalVisible = ref(false)
const importLoading = ref(false)
const importFileList = ref([])

// Batch Assign Modal
const batchAssignModalVisible = ref(false)
const batchAssignLoading = ref(false)
const selectedTeacherId = ref(null)
const teachers = ref([])

// Row selection
const rowSelection = {
  selectedRowKeys,
  onChange: (keys) => {
    selectedRowKeys.value = keys
  },
}

// Table columns
const columns = [
  {
    title: '课程名称 / Course Name',
    dataIndex: 'course_name',
    key: 'course_name',
    width: '20%',
  },
  {
    title: '学分 / Credits',
    dataIndex: 'course_credit',
    key: 'course_credit',
    width: '8%',
  },
  {
    title: '类型 / Type',
    dataIndex: 'course_type',
    key: 'course_type',
    width: '10%',
  },
  {
    title: '容量 / Capacity',
    key: 'capacity',
    width: '15%',
  },
  {
    title: '教师 / Teacher',
    key: 'teacher',
    width: '12%',
  },
  {
    title: '标签 / Tags',
    key: 'course_tags',
    width: '15%',
  },
  {
    title: '操作 / Actions',
    key: 'actions',
    width: '12%',
  },
]

// Methods
const loadCourses = async () => {
  loading.value = true
  try {
    const response = await adminApi.listCourses(
      authStore.accessToken,
      pagination.current,
      pagination.pageSize,
      searchText.value,
      filterCourseType.value
    )
    courses.value = response.courses || []
    pagination.total = response.total || 0
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录')
      authStore.logout()
    } else {
      message.error('加载课程列表失败: ' + errorDetail)
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  loadCourses()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadCourses()
}

const showEditModal = (course) => {
  Object.assign(editForm, {
    course_id: course.course_id,
    course_name: course.course_name,
    course_credit: course.course_credit,
    course_type: course.course_type,
    course_location: course.course_location,
    course_capacity: course.course_capacity,
    course_time_begin: course.course_time_begin,
    course_time_end: course.course_time_end,
    course_tags: course.course_tags || [],
    course_notes: course.course_notes || '',
    course_cost: course.course_cost || 0,
  })
  editModalVisible.value = true
}

const resetEditForm = () => {
  Object.assign(editForm, {
    course_id: null,
    course_name: '',
    course_credit: 0,
    course_type: 'required',
    course_location: '',
    course_capacity: 30,
    course_time_begin: 800,
    course_time_end: 950,
    course_tags: [],
    course_notes: '',
    course_cost: 0,
  })
  editModalVisible.value = false
}

const handleUpdateCourse = async () => {
  editLoading.value = true
  try {
    await adminApi.updateCourse(authStore.accessToken, editForm)
    message.success('课程更新成功')
    resetEditForm()
    loadCourses()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录')
      authStore.logout()
    } else {
      message.error('更新课程失败: ' + errorDetail)
    }
  } finally {
    editLoading.value = false
  }
}

const deleteCourse = async (course) => {
  try {
    await adminApi.deleteCourse(authStore.accessToken, course.course_id)
    message.success('课程删除成功')
    loadCourses()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录')
      authStore.logout()
    } else {
      message.error('删除课程失败: ' + errorDetail)
    }
  }
}

const showImportModal = () => {
  importModalVisible.value = true
}

const resetImportForm = () => {
  importFileList.value = []
  importModalVisible.value = false
}

const handleImportCourses = async () => {
  if (importFileList.value.length === 0) {
    message.error('请选择要导入的文件')
    return
  }

  importLoading.value = true
  try {
    const file = importFileList.value[0].originFileObj
    const text = await file.text()
    const lines = text.split('\n').filter(line => line.trim())
    
    if (lines.length < 2) {
      message.error('CSV 文件为空或格式不正确')
      return
    }
    
    // Parse CSV
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
    const coursesData = []
    
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''))
      const course = {
        course_name: values[headers.indexOf('course_name')] || values[0],
        course_credit: parseFloat(values[headers.indexOf('course_credit')] || values[1]) || 3,
        course_type: values[headers.indexOf('course_type')] || values[2] || 'elective',
        course_location: values[headers.indexOf('course_location')] || values[3] || 'TBD',
        course_capacity: parseInt(values[headers.indexOf('course_capacity')] || values[4]) || 30,
        course_time_begin: parseInt(values[headers.indexOf('course_time_begin')] || values[5]) || 800,
        course_time_end: parseInt(values[headers.indexOf('course_time_end')] || values[6]) || 950,
        course_tags: values[headers.indexOf('course_tags')] ? values[headers.indexOf('course_tags')].split(';').filter(t => t) : [],
        course_notes: values[headers.indexOf('course_notes')] || '',
        course_cost: parseFloat(values[headers.indexOf('course_cost')] || 0) || 0,
      }
      coursesData.push(course)
    }

    const result = await adminApi.bulkImportCourses(authStore.accessToken, coursesData)
    
    if (result.error_count > 0) {
      message.warning(`导入完成: ${result.imported_count} 成功, ${result.error_count} 失败`)
      console.log('Import errors:', result.errors)
    } else {
      message.success(`成功导入 ${result.imported_count} 门课程`)
    }
    
    resetImportForm()
    loadCourses()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录')
      authStore.logout()
    } else {
      message.error('导入课程失败: ' + errorDetail)
    }
  } finally {
    importLoading.value = false
  }
}

const exportCourses = () => {
  const selectedCourses = selectedRowKeys.value.length > 0
    ? courses.value.filter(c => selectedRowKeys.value.includes(c.course_id))
    : courses.value

  if (selectedCourses.length === 0) {
    message.warning('没有可导出的课程')
    return
  }

  // Create CSV content
  const headers = ['Course ID', 'Course Name', 'Credits', 'Type', 'Location', 'Capacity', 'Selected', 'Time Begin', 'Time End', 'Tags', 'Notes', 'Cost']
  const rows = selectedCourses.map(c => [
    c.course_id,
    c.course_name,
    c.course_credit,
    c.course_type,
    c.course_location,
    c.course_capacity,
    c.course_selected,
    c.course_time_begin,
    c.course_time_end,
    (c.course_tags || []).join(';'),
    c.course_notes || '',
    c.course_cost || 0,
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  // Download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `courses_${new Date().toISOString().split('T')[0]}.csv`
  link.click()

  message.success(`导出 ${selectedCourses.length} 门课程成功`)
}

const showBatchAssignModal = async () => {
  // Load teachers list
  try {
    const response = await adminApi.listUsers(authStore.accessToken, 'teacher', 1, 1000)
    teachers.value = response.users || []
    batchAssignModalVisible.value = true
  } catch (error) {
    message.error('加载教师列表失败: ' + (error.response?.data?.detail || error.message))
  }
}

const resetBatchAssignForm = () => {
  selectedTeacherId.value = null
  batchAssignModalVisible.value = false
}

const filterTeacherOption = (input, option) => {
  return option.children[0].children.toLowerCase().includes(input.toLowerCase())
}

const handleBatchAssignTeacher = async () => {
  if (!selectedTeacherId.value) {
    message.error('请选择教师')
    return
  }

  batchAssignLoading.value = true
  try {
    const result = await adminApi.batchAssignTeacher(
      authStore.accessToken, 
      selectedRowKeys.value, 
      selectedTeacherId.value
    )
    
    if (result.error_count > 0) {
      message.warning(`分配完成: ${result.updated_count} 成功, ${result.error_count} 失败`)
    } else {
      message.success(`成功为 ${result.updated_count} 门课程分配教师`)
    }
    
    resetBatchAssignForm()
    selectedRowKeys.value = []
    loadCourses()
  } catch (error) {
    const errorDetail = error.response?.data?.detail || error.message
    if (error.response?.status === 401 || errorDetail?.includes('Invalid token')) {
      message.error('登录已过期，请重新登录')
      authStore.logout()
    } else {
      message.error('分配教师失败: ' + errorDetail)
    }
  } finally {
    batchAssignLoading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadCourses()
})
</script>

<style scoped>
.courses-management {
  padding: 24px;
}

.card-title h2 {
  margin: 0;
  font-size: 20px;
}

.search-section {
  margin-bottom: 16px;
}

.courses-table {
  margin-top: 16px;
}
</style>
