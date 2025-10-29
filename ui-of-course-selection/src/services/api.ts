import axios from 'axios';

const loginApi = axios.create({
  baseURL: '/api/login'
});

const courseApi = axios.create({
  baseURL: '/api/course'
});

const teacherApi = axios.create({
  baseURL: '/api/teacher'
});

const studentApi = axios.create({
  baseURL: '/api/student'
});

const queueApi = axios.create({
  baseURL: '/api/queue'
});

// You can add interceptors for handling tokens here

export {
  loginApi,
  courseApi,
  teacherApi,
  studentApi,
  queueApi
};
