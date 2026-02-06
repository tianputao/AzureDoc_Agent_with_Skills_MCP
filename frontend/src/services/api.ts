import axios from 'axios';
import type { ChatRequest, ChatResponse, SkillInfo, SessionInfo } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Chat endpoints
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/chat', request);
    return response.data;
  },

  // Skills endpoints
  async listSkills(): Promise<SkillInfo[]> {
    const response = await apiClient.get<SkillInfo[]>('/skills');
    return response.data;
  },

  // Thread endpoints
  async listThreads(): Promise<SessionInfo[]> {
    const response = await apiClient.get<SessionInfo[]>('/threads');
    return response.data;
  },

  async getThreadHistory(threadId: string): Promise<{ thread_id: string; messages: any[] }> {
    const response = await apiClient.get(`/threads/${threadId}/history`);
    return response.data;
  },

  async createThread(threadId?: string): Promise<{ thread_id: string; created_at: string }> {
    const response = await apiClient.post('/threads/new', { thread_id: threadId });
    return response.data;
  },

  async deleteThread(threadId: string): Promise<void> {
    await apiClient.delete(`/threads/${threadId}`);
  },

  // Health check
  async healthCheck(): Promise<{ status: string; agent_initialized: boolean }> {
    const response = await apiClient.get('/health');
    return response.data;
  },
};
