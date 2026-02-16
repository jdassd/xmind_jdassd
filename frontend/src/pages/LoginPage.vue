<template>
  <div class="login-page">
    <div class="auth-card">
      <h1>MindMap</h1>
      <h2>Login</h2>
      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>Username</label>
          <input v-model="username" type="text" required autocomplete="username" />
        </div>
        <div class="field">
          <label>Password</label>
          <input v-model="password" type="password" required autocomplete="current-password" />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="submitting">{{ submitting ? 'Logging in...' : 'Login' }}</button>
      </form>
      <p class="switch">
        Don't have an account? <router-link to="/register">Register</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleLogin() {
  error.value = ''
  submitting.value = true
  try {
    await auth.login(username.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: any) {
    error.value = e.message || 'Login failed'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f5f5;
}

.auth-card {
  background: #fff;
  border-radius: 12px;
  padding: 40px;
  width: 380px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.auth-card h1 {
  text-align: center;
  font-size: 28px;
  color: #4a9eff;
  margin: 0 0 4px;
}

.auth-card h2 {
  text-align: center;
  font-size: 18px;
  color: #666;
  margin: 0 0 24px;
  font-weight: normal;
}

.field {
  margin-bottom: 16px;
}

.field label {
  display: block;
  font-size: 13px;
  color: #555;
  margin-bottom: 4px;
}

.field input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.field input:focus {
  border-color: #4a9eff;
}

.error {
  color: #e44;
  font-size: 13px;
  margin: 0 0 12px;
}

button[type="submit"] {
  width: 100%;
  padding: 10px;
  background: #4a9eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

button[type="submit"]:hover:not(:disabled) {
  background: #3a8eef;
}

button[type="submit"]:disabled {
  opacity: 0.6;
  cursor: default;
}

.switch {
  text-align: center;
  margin-top: 16px;
  font-size: 13px;
  color: #888;
}

.switch a {
  color: #4a9eff;
  text-decoration: none;
}
</style>
