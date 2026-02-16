<template>
  <div class="home-page">
    <div class="section">
      <h2>My Maps</h2>
      <div class="map-list">
        <div v-for="m in personalMaps" :key="m.id" class="map-item" @click="openMap(m.id)">
          <div class="map-info">
            <span class="map-name">{{ m.name }}</span>
            <span v-if="!m.owner_id" class="badge legacy">Legacy</span>
          </div>
          <div class="map-actions">
            <button v-if="!m.owner_id" class="btn-small" @click.stop="claimMap(m.id)">Claim</button>
            <button class="btn-delete" @click.stop="removeMap(m.id)">x</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="teamMaps.length > 0" class="section">
      <h2>Team Maps</h2>
      <div class="map-list">
        <div v-for="m in teamMaps" :key="m.id" class="map-item" @click="openMap(m.id)">
          <div class="map-info">
            <span class="map-name">{{ m.name }}</span>
            <span class="badge team">Team</span>
          </div>
          <button class="btn-delete" @click.stop="removeMap(m.id)">x</button>
        </div>
      </div>
    </div>

    <div class="create-form">
      <input v-model="newMapName" placeholder="New map name..." @keyup.enter="createNewMap" />
      <select v-model="selectedTeamId">
        <option value="">Personal</option>
        <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
      </select>
      <button @click="createNewMap">Create</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiJson } from '../services/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const maps = ref<any[]>([])
const teams = ref<any[]>([])
const newMapName = ref('')
const selectedTeamId = ref('')

const personalMaps = computed(() => maps.value.filter(m => !m.team_id))
const teamMaps = computed(() => maps.value.filter(m => m.team_id))

async function fetchMaps() {
  maps.value = await apiJson('/api/maps')
}

async function fetchTeams() {
  teams.value = await apiJson('/api/teams')
}

async function createNewMap() {
  const name = newMapName.value.trim()
  if (!name) return
  const body: any = { name }
  if (selectedTeamId.value) body.team_id = selectedTeamId.value
  const data = await apiJson('/api/maps', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  newMapName.value = ''
  router.push(`/map/${data.id}`)
}

function openMap(id: string) {
  router.push(`/map/${id}`)
}

async function removeMap(id: string) {
  await apiJson(`/api/maps/${id}`, { method: 'DELETE' })
  await fetchMaps()
}

async function claimMap(id: string) {
  await apiJson(`/api/maps/${id}/claim`, { method: 'POST' })
  await fetchMaps()
}

onMounted(() => {
  fetchMaps()
  fetchTeams()
})
</script>

<style scoped>
.home-page {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 18px;
  color: #333;
  margin: 0 0 12px;
}

.map-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.map-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}

.map-item:hover {
  background: #e8e8e8;
}

.map-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.map-name {
  font-size: 14px;
}

.map-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.badge.legacy {
  background: #fff3cd;
  color: #856404;
}

.badge.team {
  background: #d4edda;
  color: #155724;
}

.btn-small {
  padding: 4px 10px;
  background: #4a9eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-delete {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  padding: 2px 8px;
}

.btn-delete:hover {
  color: #e44;
}

.create-form {
  display: flex;
  gap: 8px;
  margin-top: 20px;
}

.create-form input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
}

.create-form input:focus {
  border-color: #4a9eff;
}

.create-form select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: #fff;
}

.create-form button {
  padding: 10px 20px;
  background: #4a9eff;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.create-form button:hover {
  background: #3a8eef;
}
</style>
