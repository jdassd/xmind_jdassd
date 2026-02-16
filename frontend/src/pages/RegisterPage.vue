<template>
  <div class="register-page">
    <div class="auth-card">
      <h1>MindMap</h1>
      <h2>Create Account</h2>
      <form @submit.prevent="handleRegister">
        <div class="field">
          <label>Username</label>
          <input v-model="username" type="text" required autocomplete="username" />
        </div>
        <div class="field">
          <label>Email</label>
          <input v-model="email" type="email" required autocomplete="email" />
        </div>
        <div class="field">
          <label>Display Name</label>
          <input v-model="displayName" type="text" placeholder="Optional" />
        </div>
        <div class="field">
          <label>Password</label>
          <input v-model="password" type="password" required minlength="6" autocomplete="new-password" />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="submitting">{{ submitting ? 'Creating...' : 'Register' }}</button>
      </form>
      <p class="switch">
        Already have an account? <router-link to="/login">Login</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const email = ref('')
const displayName = ref('')
const password = ref('')
const error = ref('')
const submitting = ref(false)

async function handleRegister() {
  error.value = ''
  submitting.value = true
  try {
    await auth.register(username.value, email.value, password.value, displayName.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message || 'Registration failed'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.register-page {
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
