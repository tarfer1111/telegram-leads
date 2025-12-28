export interface LoginRequestForm {
    username: string;
    password: string;
    grant_type?: 'password' | null;
    scope?: string;
    client_id?: string | null;
    client_secret?: string | null;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
    user: ManagerResponse;
}

export interface ManagerResponse {
    id: number;
    username: string;
    role: 'admin' | 'manager';
    full_name: string;
    is_active: boolean;
    created_at: string;
    projects?: ProjectInfo[];
}

export interface ManagerCreate {
    username: string;
    password: string;
    full_name: string;
}

export interface ManagerUpdate {
    password?: string | null;
    full_name?: string | null;
    is_active?: boolean | null;
}

export interface ManagerInfo {
    id: number;
    username: string;
    full_name: string;
}

export interface AddManagersRequest {
    manager_ids: number[];
}

export interface ProjectInfo {
    id: number;
    name: string;
}

export interface ProjectCreate {
    name: string;
}

export interface ProjectResponse {
    id: number;
    name: string;
    created_at: string;
}

export interface ProjectWithManagersResponse {
    id: number;
    name: string;
    created_at: string;
    managers: ManagerInfo[];
}

export interface BotCreate {
    identifier: string;
    name: string;
    token: string;
    auto_reply: string;
}

export interface BotResponse {
    id: number;
    identifier: string;
    name: string;
    project_id: number;
    token: string;
    auto_reply: string;
    webhook_url: string | null;
    is_active: boolean;
}

export interface BotUpdate {
    identifier?: string | null;
    name?: string | null;
    token?: string | null;
    auto_reply?: string | null;
    is_active?: boolean | null;
}

export interface LeadResponse {
    id: number;
    telegram_chat_id: number;
    telegram_username: string | null;
    telegram_first_name: string | null;
    telegram_last_name: string | null;
    bot_id: number;
    project_id: number;
    project_name: string;
    assigned_manager_id: number;
    // [ЗАМЕТКА] У тебя в LeadStatus есть 'read', а здесь нет.
    // Возможно, это так и задумано (фильтры vs ответ API). Оставляю как есть.
    status: 'new' | 'in_progress' | 'closed';
    created_at: string;
    last_updated_at: string;
}

export interface MessageResponse {
    id: number;
    sender: 'manager' | 'lead';
    text: string;
    created_at: string;
}

export interface SendMessageRequest {
    text: string;
}

export interface OverviewStats {
    total_leads: number;
    active_leads: number;
    closed_leads: number;
    total_messages: number;
    managers_count: number;
}

export interface ManagerStats {
    manager_id: number;
    manager_name: string;
    total_leads: number;
    active_leads: number;
    closed_leads: number;
    total_messages: number;
}

export interface DailyStats {
    date: string;
    new_leads: number;
    closed_leads: number;
    messages_count: number;
}

// [ДОБАВЛЕНО] 👇 Недостающие типы
export interface ManagerStats24h {
    manager_id: number;
    manager_name: string;
    new_leads: number;
    closed_leads: number;
    messages_count: number;
}

// [ДОБАВЛЕНО] 👇 Недостающие типы
export interface DailyManagerStats {
    date: string;
    manager_id: number;
    manager_name: string;
    new_leads: number;
    closed_leads: number;
    messages_count: number;
}

// [ДОБАВЛЕНО] 👇 Недостающие типы
export interface GetDailyManagerStatsParams {
    days?: number;
    start_date?: string;
    end_date?: string;
    manager_id?: number;
}

export interface ValidationError {
    loc: (string | number)[];
    msg: string;
    type: string;
}

export interface HTTPValidationError {
    detail?: ValidationError[];
}

export type LeadStatus = 'new' | 'read' | 'in_progress' | 'closed';