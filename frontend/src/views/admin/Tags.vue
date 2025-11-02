<template>
  <div class="tags-management">
    <a-card>
      <template #title>
        <div class="card-title">
          <h2>标签管理 / Tag Management</h2>
        </div>
      </template>

      <a-tabs v-model:activeKey="activeTab">
        <!-- User Tags Tab -->
        <a-tab-pane key="user" tab="用户标签 / User Tags">
          <a-card size="small" style="margin-bottom: 16px;">
            <a-space direction="vertical" style="width: 100%;">
              <div>
                <h3>添加用户标签 / Add User Tags</h3>
                <a-space>
                  <a-select
                    v-model:value="selectedUserIds"
                    mode="multiple"
                    placeholder="选择用户 / Select users"
                    style="width: 300px;"
                    show-search
                    :filter-option="filterUserOption"
                    @search="handleUserSearch"
                  >
                    <a-select-option v-for="user in users" :key="user.user_id" :value="user.user_id">
                      {{ user.username }} ({{ user.user_type }})
                    </a-select-option>
                  </a-select>
                  
                  <a-select
                    v-model:value="newUserTags"
                    mode="tags"
                    placeholder="输入标签 / Enter tags"
                    style="width: 300px;"
                    :options="availableUserTags.map(tag => ({ label: tag, value: tag }))"
                    @search="handleUserTagSearch"
                  />
                  
                  <a-button type="primary" @click="addUserTags" :loading="userTagsLoading">
                    添加标签
                  </a-button>
                </a-space>
              </div>

              <a-divider />

              <div>
                <h3>现有用户标签 / Existing User Tags</h3>
                <div v-if="userTagsStats.length > 0">
                  <a-space wrap>
                    <a-tag
                      v-for="tagStat in userTagsStats"
                      :key="tagStat.tag"
                      color="blue"
                      closable
                      @close="removeUserTag(tagStat.tag)"
                    >
                      {{ tagStat.tag }} ({{ tagStat.count }} 用户)
                    </a-tag>
                  </a-space>
                </div>
                <a-empty v-else description="暂无用户标签" />
              </div>

              <a-divider />

              <div>
                <h3>批量操作 / Batch Operations</h3>
                <a-space>
                  <a-button @click="showBatchImportUserTagModal">
                    批量导入用户标签
                  </a-button>
                  <a-button @click="showBatchRemoveUserTagModal">
                    批量移除用户标签
                  </a-button>
                  <a-button @click="showBatchReplaceUserTagModal">
                    批量替换用户标签
                  </a-button>
                </a-space>
              </div>
            </a-space>
          </a-card>

          <!-- Filter Section -->
          <div style="margin-bottom: 16px;">
            <a-space>
              <span>按标签筛选 / Filter by Tag:</span>
              <a-select
                v-model:value="userTagFilter"
                placeholder="全部 / All"
                style="width: 200px;"
                allow-clear
              >
                <a-select-option :value="null">全部 / All</a-select-option>
                <a-select-option v-for="tagStat in userTagsStats" :key="tagStat.tag" :value="tagStat.tag">
                  {{ tagStat.tag }} ({{ tagStat.count }})
                </a-select-option>
              </a-select>
            </a-space>
          </div>

          <!-- Users with Tags Table -->
          <a-table
            :columns="userTagsColumns"
            :data-source="filteredUsersWithTags"
            :loading="userTagsTableLoading"
            :pagination="userTagsPagination"
            @change="handleUserTagsTableChange"
            row-key="user_id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'tags'">
                <a-tag v-for="tag in record.student_tags" :key="tag" color="green">
                  {{ tag }}
                </a-tag>
                <span v-if="!record.student_tags || record.student_tags.length === 0" style="color: #999;">无标签</span>
              </template>
            </template>
          </a-table>
        </a-tab-pane>

        <!-- Course Tags Tab -->
        <a-tab-pane key="course" tab="课程标签 / Course Tags">
          <a-card size="small" style="margin-bottom: 16px;">
            <a-space direction="vertical" style="width: 100%;">
              <div>
                <h3>添加课程标签 / Add Course Tags</h3>
                <a-space>
                  <a-select
                    v-model:value="selectedCourseIds"
                    mode="multiple"
                    placeholder="选择课程 / Select courses"
                    style="width: 300px;"
                    show-search
                    :filter-option="filterCourseOption"
                    @search="handleCourseSearch"
                  >
                    <a-select-option v-for="course in courses" :key="course.course_id" :value="course.course_id">
                      {{ course.course_name }}
                    </a-select-option>
                  </a-select>
                  
                  <a-select
                    v-model:value="newCourseTags"
                    mode="tags"
                    placeholder="输入标签 / Enter tags"
                    style="width: 300px;"
                    :options="availableCourseTags.map(tag => ({ label: tag, value: tag }))"
                    @search="handleCourseTagSearch"
                  />
                  
                  <a-button type="primary" @click="addCourseTags" :loading="courseTagsLoading">
                    添加标签
                  </a-button>
                </a-space>
              </div>

              <a-divider />

              <div>
                <h3>现有课程标签 / Existing Course Tags</h3>
                <div v-if="courseTagsStats.length > 0">
                  <a-space wrap>
                    <a-tag
                      v-for="tagStat in courseTagsStats"
                      :key="tagStat.tag"
                      color="orange"
                      closable
                      @close="removeCourseTag(tagStat.tag)"
                    >
                      {{ tagStat.tag }} ({{ tagStat.count }} 课程)
                    </a-tag>
                  </a-space>
                </div>
                <a-empty v-else description="暂无课程标签" />
              </div>

              <a-divider />

              <div>
                <h3>批量操作 / Batch Operations</h3>
                <a-space>
                  <a-button @click="showBatchImportCourseTagModal">
                    批量导入课程标签
                  </a-button>
                  <a-button @click="showBatchRemoveCourseTagModal">
                    批量移除课程标签
                  </a-button>
                  <a-button @click="showBatchReplaceCourseTagModal">
                    批量替换课程标签
                  </a-button>
                </a-space>
              </div>
            </a-space>
          </a-card>

          <!-- Filter and Search Section -->
          <div style="margin-bottom: 16px;">
            <a-space>
              <span>按标签筛选 / Filter by Tag:</span>
              <a-select
                v-model:value="courseTagFilter"
                placeholder="全部 / All"
                style="width: 200px;"
                allow-clear
              >
                <a-select-option :value="null">全部 / All</a-select-option>
                <a-select-option v-for="tagStat in courseTagsStats" :key="tagStat.tag" :value="tagStat.tag">
                  {{ tagStat.tag }} ({{ tagStat.count }})
                </a-select-option>
              </a-select>
              
              <span style="margin-left: 16px;">搜索课程 / Search Course:</span>
              <a-input-search
                v-model:value="courseSearchText"
                placeholder="输入课程名称 / Enter course name"
                style="width: 300px;"
                allow-clear
              />
            </a-space>
          </div>

          <!-- Courses with Tags Table -->
          <a-table
            :columns="courseTagsColumns"
            :data-source="filteredCoursesWithTags"
            :loading="courseTagsTableLoading"
            :pagination="courseTagsPagination"
            @change="handleCourseTagsTableChange"
            row-key="course_id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'tags'">
                <a-tag v-for="tag in record.course_tags" :key="tag" color="orange">
                  {{ tag }}
                </a-tag>
                <span v-if="!record.course_tags || record.course_tags.length === 0" style="color: #999;">无标签</span>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- Batch Import User Tag Modal -->
    <a-modal
      v-model:open="batchImportUserTagModalVisible"
      title="批量导入用户标签 / Batch Import User Tags"
      @ok="handleBatchImportUserTag"
      :confirm-loading="batchOperationLoading"
      width="700px"
    >
      <a-form layout="vertical">
        <a-form-item label="CSV 数据 / CSV Data">
          <a-textarea
            v-model:value="batchImportUserTagText"
            placeholder="格式 / Format: username,tag1,tag2,...,tagn&#10;例如 / Example:&#10;student1,math,science&#10;student2,english,history,art"
            :rows="10"
          />
        </a-form-item>
        <a-alert
          message="格式说明 / Format"
          description="每行一个用户，格式为：用户名,标签1,标签2,...,标签n。标签将被添加到用户现有标签中（不会覆盖）。Each line: username,tag1,tag2,...,tagn. Tags will be added to existing user tags."
          type="info"
          show-icon
          style="margin-top: 8px;"
        />
      </a-form>
    </a-modal>

    <!-- Batch Remove User Tag Modal -->
    <a-modal
      v-model:open="batchRemoveUserTagModalVisible"
      title="批量移除用户标签 / Batch Remove User Tag"
      @ok="handleBatchRemoveUserTag"
      :confirm-loading="batchOperationLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="选择要移除的标签 / Select tag to remove">
          <a-select v-model:value="batchRemoveUserTagValue" style="width: 100%;">
            <a-select-option v-for="tagStat in userTagsStats" :key="tagStat.tag" :value="tagStat.tag">
              {{ tagStat.tag }} ({{ tagStat.count }} 用户)
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Batch Replace User Tag Modal -->
    <a-modal
      v-model:open="batchReplaceUserTagModalVisible"
      title="批量替换用户标签 / Batch Replace User Tag"
      @ok="handleBatchReplaceUserTag"
      :confirm-loading="batchOperationLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="原标签 / Old tag">
          <a-select v-model:value="batchReplaceUserTagOld" style="width: 100%;">
            <a-select-option v-for="tagStat in userTagsStats" :key="tagStat.tag" :value="tagStat.tag">
              {{ tagStat.tag }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="新标签 / New tag">
          <a-input v-model:value="batchReplaceUserTagNew" placeholder="Enter new tag" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Batch Import Course Tag Modal -->
    <a-modal
      v-model:open="batchImportCourseTagModalVisible"
      title="批量导入课程标签 / Batch Import Course Tags"
      @ok="handleBatchImportCourseTag"
      :confirm-loading="batchOperationLoading"
      width="700px"
    >
      <a-form layout="vertical">
        <a-form-item label="CSV 数据 / CSV Data">
          <a-textarea
            v-model:value="batchImportCourseTagText"
            placeholder="格式 / Format: course_name,tag1,tag2,...,tagn&#10;例如 / Example:&#10;数学,math,science&#10;英语,english,language"
            :rows="10"
          />
        </a-form-item>
        <a-alert
          message="格式说明 / Format"
          description="每行一门课程，格式为：课程名,标签1,标签2,...,标签n。标签将被添加到课程现有标签中。Each line: course_name,tag1,tag2,...,tagn. Tags will be added to existing course tags."
          type="info"
          show-icon
          style="margin-top: 8px;"
        />
      </a-form>
    </a-modal>

    <!-- Batch Remove Course Tag Modal -->
    <a-modal
      v-model:open="batchRemoveCourseTagModalVisible"
      title="批量移除课程标签 / Batch Remove Course Tag"
      @ok="handleBatchRemoveCourseTag"
      :confirm-loading="batchOperationLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="选择要移除的标签 / Select tag to remove">
          <a-select v-model:value="batchRemoveCourseTagValue" style="width: 100%;">
            <a-select-option v-for="tagStat in courseTagsStats" :key="tagStat.tag" :value="tagStat.tag">
              {{ tagStat.tag }} ({{ tagStat.count }} 课程)
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Batch Replace Course Tag Modal -->
    <a-modal
      v-model:open="batchReplaceCourseTagModalVisible"
      title="批量替换课程标签 / Batch Replace Course Tag"
      @ok="handleBatchReplaceCourseTag"
      :confirm-loading="batchOperationLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="原标签 / Old tag">
          <a-select v-model:value="batchReplaceCourseTagOld" style="width: 100%;">
            <a-select-option v-for="tagStat in courseTagsStats" :key="tagStat.tag" :value="tagStat.tag">
              {{ tagStat.tag }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="新标签 / New tag">
          <a-input v-model:value="batchReplaceCourseTagNew" placeholder="Enter new tag" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/store/auth'
import adminApi from '@/api/admin'

const authStore = useAuthStore()

// State
const activeTab = ref('user')
const userTagsLoading = ref(false)
const courseTagsLoading = ref(false)
const userTagsTableLoading = ref(false)
const courseTagsTableLoading = ref(false)
const batchOperationLoading = ref(false)

// Available tags for autocomplete
const availableUserTags = ref([])
const availableCourseTags = ref([])

// User Tags
const users = ref([])
const selectedUserIds = ref([])
const newUserTags = ref([])
const usersWithTags = ref([])
const userTagFilter = ref(null) // Filter users by tag
const userTagsPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

// Course Tags
const courses = ref([])
const selectedCourseIds = ref([])
const newCourseTags = ref([])
const coursesWithTags = ref([])
const courseTagFilter = ref(null) // Filter courses by tag
const courseSearchText = ref('') // Search courses by name
const courseTagsPagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

// Batch modals
const batchImportUserTagModalVisible = ref(false)
const batchImportUserTagText = ref('')
const batchRemoveUserTagModalVisible = ref(false)
const batchRemoveUserTagValue = ref(null)
const batchReplaceUserTagModalVisible = ref(false)
const batchReplaceUserTagOld = ref(null)
const batchReplaceUserTagNew = ref('')

const batchImportCourseTagModalVisible = ref(false)
const batchImportCourseTagText = ref('')
const batchRemoveCourseTagModalVisible = ref(false)
const batchRemoveCourseTagValue = ref(null)
const batchReplaceCourseTagModalVisible = ref(false)
const batchReplaceCourseTagOld = ref(null)
const batchReplaceCourseTagNew = ref('')

// Columns
const userTagsColumns = [
  { title: 'User ID', dataIndex: 'user_id', key: 'user_id' },
  { title: 'Username', dataIndex: 'username', key: 'username' },
  { title: 'Type', dataIndex: 'user_type', key: 'user_type' },
  { title: 'Tags', key: 'tags' },
]

const courseTagsColumns = [
  { title: 'Course ID', dataIndex: 'course_id', key: 'course_id' },
  { title: 'Course Name', dataIndex: 'course_name', key: 'course_name' },
  { title: 'Type', dataIndex: 'course_type', key: 'course_type' },
  { title: 'Tags', key: 'tags' },
]

// Computed statistics
const userTagsStats = computed(() => {
  if (!usersWithTags.value || !Array.isArray(usersWithTags.value)) {
    return []
  }
  const tagMap = new Map()
  usersWithTags.value.forEach(user => {
    if (user && user.student_tags && Array.isArray(user.student_tags)) {
      user.student_tags.forEach(tag => {
        if (tag) {
          tagMap.set(tag, (tagMap.get(tag) || 0) + 1)
        }
      })
    }
  })
  return Array.from(tagMap.entries())
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => b.count - a.count)
})

const courseTagsStats = computed(() => {
  if (!coursesWithTags.value || !Array.isArray(coursesWithTags.value)) {
    return []
  }
  const tagMap = new Map()
  coursesWithTags.value.forEach(course => {
    if (course && course.course_tags && Array.isArray(course.course_tags)) {
      course.course_tags.forEach(tag => {
        if (tag) {
          tagMap.set(tag, (tagMap.get(tag) || 0) + 1)
        }
      })
    }
  })
  return Array.from(tagMap.entries())
    .map(([tag, count]) => ({ tag, count }))
    .sort((a, b) => b.count - a.count)
})

// Filtered users with tags
const filteredUsersWithTags = computed(() => {
  if (!usersWithTags.value || !Array.isArray(usersWithTags.value)) {
    return []
  }
  if (!userTagFilter.value) {
    return usersWithTags.value
  }
  return usersWithTags.value.filter(user => {
    return user && user.student_tags && Array.isArray(user.student_tags) && user.student_tags.includes(userTagFilter.value)
  })
})

// Filtered courses with tags
const filteredCoursesWithTags = computed(() => {
  if (!coursesWithTags.value || !Array.isArray(coursesWithTags.value)) {
    return []
  }
  let filtered = coursesWithTags.value
  
  // Filter by tag
  if (courseTagFilter.value) {
    filtered = filtered.filter(course => {
      return course && course.course_tags && Array.isArray(course.course_tags) && course.course_tags.includes(courseTagFilter.value)
    })
  }
  
  // Filter by search text
  if (courseSearchText.value) {
    const searchLower = courseSearchText.value.toLowerCase()
    filtered = filtered.filter(course => {
      return course && course.course_name && course.course_name.toLowerCase().includes(searchLower)
    })
  }
  
  return filtered
})

// Methods
const loadAvailableTags = async () => {
  try {
    // Load user tags
    const userTagsResponse = await adminApi.getAvailableTags(authStore.accessToken, 'user')
    availableUserTags.value = (userTagsResponse.tags || []).map(t => t.tag_name)
    
    // Load course tags
    const courseTagsResponse = await adminApi.getAvailableTags(authStore.accessToken, 'course')
    availableCourseTags.value = (courseTagsResponse.tags || []).map(t => t.tag_name)
  } catch (error) {
    console.error('Failed to load available tags:', error)
  }
}

const loadUsers = async () => {
  try {
    const response = await adminApi.listUsers(authStore.accessToken, 'student', 1, 1000)
    users.value = response.users || []
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

const loadUsersWithTags = async () => {
  userTagsTableLoading.value = true
  try {
    const response = await adminApi.listUsers(
      authStore.accessToken,
      'student',
      userTagsPagination.current,
      userTagsPagination.pageSize
    )
    usersWithTags.value = response.users || []
    userTagsPagination.total = response.total || 0
  } catch (error) {
    message.error('加载用户失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    userTagsTableLoading.value = false
  }
}

const loadCourses = async () => {
  try {
    const response = await adminApi.listCourses(authStore.accessToken, 1, 1000)
    courses.value = response.courses || []
  } catch (error) {
    console.error('Failed to load courses:', error)
  }
}

const loadCoursesWithTags = async () => {
  courseTagsTableLoading.value = true
  try {
    const response = await adminApi.listCourses(
      authStore.accessToken,
      courseTagsPagination.current,
      courseTagsPagination.pageSize
    )
    coursesWithTags.value = response.courses || []
    courseTagsPagination.total = response.total || 0
  } catch (error) {
    message.error('加载课程失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    courseTagsTableLoading.value = false
  }
}

const addUserTags = async () => {
  if (selectedUserIds.value.length === 0 || newUserTags.value.length === 0) {
    message.warning('请选择用户和标签')
    return
  }

  userTagsLoading.value = true
  try {
    for (const userId of selectedUserIds.value) {
      const user = users.value.find(u => u.user_id === userId)
      const existingTags = user?.student_tags || []
      const updatedTags = [...new Set([...existingTags, ...newUserTags.value])]
      
      await adminApi.updateStudentTags(authStore.accessToken, userId, updatedTags)
    }
    
    message.success(`成功为 ${selectedUserIds.value.length} 个用户添加标签`)
    selectedUserIds.value = []
    newUserTags.value = []
    await loadAvailableTags()
    await loadUsers()
    await loadUsersWithTags()
  } catch (error) {
    message.error('添加标签失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    userTagsLoading.value = false
  }
}

const removeUserTag = async (tag) => {
  const affectedUsers = usersWithTags.value.filter(u => 
    (u.student_tags || []).includes(tag)
  )
  
  try {
    for (const user of affectedUsers) {
      const updatedTags = (user.student_tags || []).filter(t => t !== tag)
      await adminApi.updateStudentTags(authStore.accessToken, user.user_id, updatedTags)
    }
    
    message.success(`已从 ${affectedUsers.length} 个用户中移除标签 "${tag}"`)
    await loadAvailableTags()
    await loadUsers()
    await loadUsersWithTags()
  } catch (error) {
    message.error('移除标签失败: ' + (error.response?.data?.detail || error.message))
  }
}

const addCourseTags = async () => {
  if (selectedCourseIds.value.length === 0 || newCourseTags.value.length === 0) {
    message.warning('请选择课程和标签')
    return
  }

  courseTagsLoading.value = true
  try {
    for (const courseId of selectedCourseIds.value) {
      const course = courses.value.find(c => c.course_id === courseId)
      const existingTags = course?.course_tags || []
      const updatedTags = [...new Set([...existingTags, ...newCourseTags.value])]
      
      await adminApi.updateCourse(authStore.accessToken, {
        course_id: courseId,
        course_tags: updatedTags
      })
    }
    
    message.success(`成功为 ${selectedCourseIds.value.length} 门课程添加标签`)
    selectedCourseIds.value = []
    newCourseTags.value = []
    await loadAvailableTags()
    await loadCourses()
    await loadCoursesWithTags()
  } catch (error) {
    message.error('添加标签失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    courseTagsLoading.value = false
  }
}

const removeCourseTag = async (tag) => {
  const affectedCourses = coursesWithTags.value.filter(c => 
    (c.course_tags || []).includes(tag)
  )
  
  try {
    for (const course of affectedCourses) {
      const updatedTags = (course.course_tags || []).filter(t => t !== tag)
      await adminApi.updateCourse(authStore.accessToken, {
        course_id: course.course_id,
        course_tags: updatedTags
      })
    }
    
    message.success(`已从 ${affectedCourses.length} 门课程中移除标签 "${tag}"`)
    await loadAvailableTags()
    await loadCourses()
    await loadCoursesWithTags()
  } catch (error) {
    message.error('移除标签失败: ' + (error.response?.data?.detail || error.message))
  }
}

// Batch operations
const showBatchImportUserTagModal = () => {
  batchImportUserTagModalVisible.value = true
}

const handleBatchImportUserTag = async () => {
  if (!batchImportUserTagText.value || !batchImportUserTagText.value.trim()) {
    message.warning('请输入CSV数据')
    return
  }
  
  batchOperationLoading.value = true
  try {
    const result = await adminApi.batchImportUserTags(authStore.accessToken, batchImportUserTagText.value)
    
    if (result.failed_count > 0) {
      message.warning(`导入完成: ${result.imported_count} 成功, ${result.failed_count} 失败`)
      console.log('Import errors:', result.details.failed)
    } else {
      message.success(`成功导入 ${result.imported_count} 个用户的标签`)
    }
    
    batchImportUserTagModalVisible.value = false
    batchImportUserTagText.value = ''
    await loadAvailableTags()
    await loadUsers()
    await loadUsersWithTags()
  } catch (error) {
    message.error('批量导入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    batchOperationLoading.value = false
  }
}

const showBatchRemoveUserTagModal = () => {
  batchRemoveUserTagModalVisible.value = true
}

const handleBatchRemoveUserTag = async () => {
  if (!batchRemoveUserTagValue.value) {
    message.warning('请选择标签')
    return
  }
  
  batchOperationLoading.value = true
  try {
    await removeUserTag(batchRemoveUserTagValue.value)
    batchRemoveUserTagModalVisible.value = false
    batchRemoveUserTagValue.value = null
  } finally {
    batchOperationLoading.value = false
  }
}

const showBatchReplaceUserTagModal = () => {
  batchReplaceUserTagModalVisible.value = true
}

const handleBatchReplaceUserTag = async () => {
  if (!batchReplaceUserTagOld.value || !batchReplaceUserTagNew.value) {
    message.warning('请填写原标签和新标签')
    return
  }
  
  batchOperationLoading.value = true
  try {
    const affectedUsers = usersWithTags.value.filter(u => 
      (u.student_tags || []).includes(batchReplaceUserTagOld.value)
    )
    
    for (const user of affectedUsers) {
      const updatedTags = (user.student_tags || []).map(t => 
        t === batchReplaceUserTagOld.value ? batchReplaceUserTagNew.value : t
      )
      await adminApi.updateStudentTags(authStore.accessToken, user.user_id, updatedTags)
    }
    
    message.success(`已为 ${affectedUsers.length} 个用户替换标签`)
    batchReplaceUserTagModalVisible.value = false
    batchReplaceUserTagOld.value = null
    batchReplaceUserTagNew.value = ''
    await loadAvailableTags()
    await loadUsers()
    await loadUsersWithTags()
  } catch (error) {
    message.error('替换标签失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    batchOperationLoading.value = false
  }
}

const showBatchImportCourseTagModal = () => {
  batchImportCourseTagModalVisible.value = true
}

const handleBatchImportCourseTag = async () => {
  if (!batchImportCourseTagText.value || !batchImportCourseTagText.value.trim()) {
    message.warning('请输入CSV数据')
    return
  }
  
  batchOperationLoading.value = true
  try {
    // Parse CSV and update courses
    const lines = batchImportCourseTagText.value.trim().split('\n')
    let successCount = 0
    let failCount = 0
    const errors = []
    
    for (const line of lines) {
      if (!line.trim()) continue
      
      const parts = line.split(',').map(p => p.trim())
      if (parts.length < 2) {
        failCount++
        errors.push({ line, error: 'Invalid format' })
        continue
      }
      
      const courseName = parts[0]
      const tags = parts.slice(1).filter(t => t)
      
      // Find course by name
      const course = coursesWithTags.value.find(c => c.course_name === courseName)
      if (!course) {
        failCount++
        errors.push({ line, error: `Course "${courseName}" not found` })
        continue
      }
      
      try {
        const existingTags = course.course_tags || []
        const updatedTags = [...new Set([...existingTags, ...tags])]
        
        await adminApi.updateCourse(authStore.accessToken, {
          course_id: course.course_id,
          course_tags: updatedTags
        })
        successCount++
      } catch (error) {
        failCount++
        errors.push({ line, error: error.message })
      }
    }
    
    if (failCount > 0) {
      message.warning(`导入完成: ${successCount} 成功, ${failCount} 失败`)
      console.log('Import errors:', errors)
    } else {
      message.success(`成功导入 ${successCount} 门课程的标签`)
    }
    
    batchImportCourseTagModalVisible.value = false
    batchImportCourseTagText.value = ''
    await loadAvailableTags()
    await loadCourses()
    await loadCoursesWithTags()
  } catch (error) {
    message.error('批量导入失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    batchOperationLoading.value = false
  }
}

const showBatchRemoveCourseTagModal = () => {
  batchRemoveCourseTagModalVisible.value = true
}

const handleBatchRemoveCourseTag = async () => {
  if (!batchRemoveCourseTagValue.value) {
    message.warning('请选择标签')
    return
  }
  
  batchOperationLoading.value = true
  try {
    await removeCourseTag(batchRemoveCourseTagValue.value)
    batchRemoveCourseTagModalVisible.value = false
    batchRemoveCourseTagValue.value = null
  } finally {
    batchOperationLoading.value = false
  }
}

const showBatchReplaceCourseTagModal = () => {
  batchReplaceCourseTagModalVisible.value = true
}

const handleBatchReplaceCourseTag = async () => {
  if (!batchReplaceCourseTagOld.value || !batchReplaceCourseTagNew.value) {
    message.warning('请填写原标签和新标签')
    return
  }
  
  batchOperationLoading.value = true
  try {
    const affectedCourses = coursesWithTags.value.filter(c => 
      (c.course_tags || []).includes(batchReplaceCourseTagOld.value)
    )
    
    for (const course of affectedCourses) {
      const updatedTags = (course.course_tags || []).map(t => 
        t === batchReplaceCourseTagOld.value ? batchReplaceCourseTagNew.value : t
      )
      await adminApi.updateCourse(authStore.accessToken, {
        course_id: course.course_id,
        course_tags: updatedTags
      })
    }
    
    message.success(`已为 ${affectedCourses.length} 门课程替换标签`)
    batchReplaceCourseTagModalVisible.value = false
    batchReplaceCourseTagOld.value = null
    batchReplaceCourseTagNew.value = ''
    await loadAvailableTags()
    await loadCourses()
    await loadCoursesWithTags()
  } catch (error) {
    message.error('替换标签失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    batchOperationLoading.value = false
  }
}

// Table handlers
const handleUserTagsTableChange = (pag) => {
  userTagsPagination.current = pag.current
  userTagsPagination.pageSize = pag.pageSize
  loadUsersWithTags()
}

const handleCourseTagsTableChange = (pag) => {
  courseTagsPagination.current = pag.current
  courseTagsPagination.pageSize = pag.pageSize
  loadCoursesWithTags()
}

// Search filters
const filterUserOption = (input, option) => {
  return option.children[0].children.toLowerCase().includes(input.toLowerCase())
}

const filterCourseOption = (input, option) => {
  return option.children[0].children.toLowerCase().includes(input.toLowerCase())
}

const handleUserSearch = (value) => {
  // Implement search if needed
}

const handleCourseSearch = (value) => {
  // Implement search if needed
}

const handleUserTagSearch = (value) => {
  // This is called when typing in the user tags select
  // The autocomplete will filter automatically based on available options
}

const handleCourseTagSearch = (value) => {
  // This is called when typing in the course tags select
  // The autocomplete will filter automatically based on available options
}

// Lifecycle
onMounted(() => {
  loadAvailableTags()
  loadUsers()
  loadUsersWithTags()
  loadCourses()
  loadCoursesWithTags()
})
</script>

<style scoped>
.tags-management {
  padding: 24px;
}

.card-title h2 {
  margin: 0;
  font-size: 20px;
}
</style>
