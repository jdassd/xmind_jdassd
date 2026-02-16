<template>
  <div class="team-detail-page">
    <div v-if="team" class="content">
      <div class="team-header">
        <div v-if="!editingName" class="team-title">
          <h2>{{ team.name }}</h2>
          <button v-if="isAdmin" class="btn-icon" @click="editingName = true">Edit</button>
        </div>
        <div v-else class="edit-name">
          <input v-model="editName" @keyup.enter="saveName" />
          <button @click="saveName">Save</button>
          <button @click="editingName = false">Cancel</button>
        </div>
        <router-link to="/teams" class="back-link">Back to Teams</router-link>
      </div>

      <div class="section">
        <h3>Members ({{ members.length }})</h3>
        <div class="member-list">
          <div v-for="m in members" :key="m.id" class="member-item">
            <div class="member-info">
              <span class="member-name">{{ m.display_name || m.username }}</span>
              <span class="member-email">{{ m.email }}</span>
            </div>
            <div class="member-actions">
              <select
                v-if="isAdmin && m.role !== 'owner'"
                :value="m.role"
                @change="changeRole(m.id, ($event.target as HTMLSelectElement).value)"
              >
                <option value="admin">admin</option>
                <option value="editor">editor</option>
                <option value="viewer">viewer</option>
              </select>
              <span v-else class="role-badge">{{ m.role }}</span>
              <button
                v-if="isAdmin && m.role !== 'owner'"
                class="btn-remove"
                @click="removeMember(m.id)"
              >Remove</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isAdmin" class="section">
        <h3>Invite Member</h3>
        <div class="invite-form">
          <input v-model="inviteEmail" type="email" placeholder="Email address" />
          <select v-model="inviteRole">
            <option value="viewer">viewer</option>
            <option value="editor">editor</option>
            <option value="admin">admin</option>
          </select>
          <button @click="inviteMember">Invite</button>
        </div>
        <p v-if="inviteError" class="error">{{ inviteError }}</p>
        <p v-if="inviteSuccess" class="success">{{ inviteSuccess }}</p>
      </div>

      <div class="section">
        <h3>Team Maps</h3>
        <div class="map-list">
          <div v-for="m in teamMaps" :key="m.id" class="map-item" @click="router.push(`/map/${m.id}`)">
            <span>{{ m.name }}</span>
          </div>
          <p v-if="teamMaps.length === 0" class="empty">No maps in this team yet.</p>
        </div>
      </div>
    </div>
    <div v-else class="loading">Loading...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiJson } from '../services/api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const team = ref<any>(null)
const members = ref<any[]>([])
const teamMaps = ref<any[]>([])
const editingName = ref(false)
const editName = ref('')
const inviteEmail = ref('')
const inviteRole = ref('viewer')
const inviteError = ref('')
const inviteSuccess = ref('')

const teamId = computed(() => route.params.id as string)

const myRole = computed(() => {
  const me = members.value.find(m => m.id === auth.user?.id)
  return me?.role || ''
})

const isAdmin = computed(() => ['owner', 'admin'].includes(myRole.value))

async function fetchTeam() {
  team.value = await apiJson(`/api/teams/${teamId.value}`)
  editName.value = team.value.name
}

async function fetchMembers() {
  members.value = await apiJson(`/api/teams/${teamId.value}/members`)
}

async function fetchTeamMaps() {
  const allMaps = await apiJson('/api/maps')
  teamMaps.value = allMaps.filter((m: any) => m.team_id === teamId.value)
}

async function saveName() {
  await apiJson(`/api/teams/${teamId.value}`, {
    method: 'PUT',
    body: JSON.stringify({ name: editName.value }),
  })
  team.value.name = editName.value
  editingName.value = false
}

async function changeRole(memberId: string, role: string) {
  await apiJson(`/api/teams/${teamId.value}/members/${memberId}`, {
    method: 'PUT',
    body: JSON.stringify({ role }),
  })
  await fetchMembers()
}

async function removeMember(memberId: string) {
  await apiJson(`/api/teams/${teamId.value}/members/${memberId}`, { method: 'DELETE' })
  await fetchMembers()
}

async function inviteMember() {
  inviteError.value = ''
  inviteSuccess.value = ''
  try {
    await apiJson(`/api/teams/${teamId.value}/members`, {
      method: 'POST',
      body: JSON.stringify({ email: inviteEmail.value, role: inviteRole.value }),
    })
    inviteSuccess.value = `Invitation sent to ${inviteEmail.value}`
    inviteEmail.value = ''
  } catch (e: any) {
    inviteError.value = e.message
  }
}

onMounted(() => {
  fetchTeam()
  fetchMembers()
  fetchTeamMaps()
})
</script>

<style scoped>
.team-detail-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 40px 20px;
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.team-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.team-title h2 {
  font-size: 24px;
  color: #333;
  margin: 0;
}

.btn-icon {
  padding: 4px 10px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  color: #666;
}

.edit-name {
  display: flex;
  gap: 8px;
  align-items: center;
}

.edit-name input {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.edit-name button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  background: #fff;
}

.back-link {
  font-size: 13px;
  color: #4a9eff;
  text-decoration: none;
}

.section {
  margin-bottom: 32px;
}

.section h3 {
  font-size: 16px;
  color: #333;
  margin: 0 0 12px;
}

.member-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.member-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f5f5f5;
  border-radius: 6px;
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.member-name {
  font-size: 14px;
  font-weight: 500;
}

.member-email {
  font-size: 12px;
  color: #888;
}

.member-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-actions select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
}

.role-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: #e2e3e5;
  border-radius: 4px;
}

.btn-remove {
  padding: 4px 10px;
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  color: #e44;
  cursor: pointer;
}

.btn-remove:hover {
  border-color: #e44;
  background: #fee;
}

.invite-form {
  display: flex;
  gap: 8px;
}

.invite-form input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

.invite-form select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
}

.invite-form button {
  padding: 8px 16px;
  background: #4a9eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.error {
  color: #e44;
  font-size: 13px;
  margin-top: 8px;
}

.success {
  color: #28a745;
  font-size: 13px;
  margin-top: 8px;
}

.map-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.map-item {
  padding: 10px 14px;
  background: #f5f5f5;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.map-item:hover {
  background: #e8e8e8;
}

.empty {
  color: #888;
  font-size: 13px;
}

.loading {
  text-align: center;
  padding: 80px;
  color: #888;
}
</style>
