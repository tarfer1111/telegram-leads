import api from './api';
import type { LeadResponse, MessageResponse, SendMessageRequest } from '@/types/api.types';

export type LeadStatus = 'new' | 'read' | 'in_progress' | 'closed';
export async function getLeads(status?: LeadStatus | ''): Promise<LeadResponse[]> {
    const response = await api.get<LeadResponse[]>('/leads', {
        params: {
            status: status || undefined
        }
    });
    return response.data;
}

export async function getLeadDetails(leadId: number): Promise<LeadResponse> {
    const response = await api.get<LeadResponse>(`/leads/${leadId}`);
    return response.data;
}

export async function closeLead(leadId: number): Promise<void> {
    await api.put(`/leads/${leadId}/close`);
}

export async function getMessages(leadId: number): Promise<MessageResponse[]> {
    const response = await api.get<MessageResponse[]>(`/messages/${leadId}`);
    return response.data;
}

export async function sendMessage(leadId: number, message: SendMessageRequest): Promise<void> {
    await api.post(`/messages/${leadId}/send`, message);
}

export async function markLeadAsRead(leadId: number): Promise<void> {
    await api.put(`/leads/${leadId}/mark-read`);
}