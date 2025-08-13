-- Row Level Security Policies for Amazon AMC Manager (Fixed for JSONB)

-- Note: These policies assume you're using Supabase Auth
-- If using custom JWT auth, replace auth.uid() with auth.jwt() ->> 'sub' or similar

-- Users policies
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Service role can manage all users" ON users
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- AMC Accounts policies
CREATE POLICY "Users can view own accounts" ON amc_accounts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own accounts" ON amc_accounts
    FOR ALL USING (auth.uid() = user_id);

-- AMC Instances policies
CREATE POLICY "Users can view instances for their accounts" ON amc_instances
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM amc_accounts 
            WHERE amc_accounts.id = amc_instances.account_id 
            AND amc_accounts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage instances for their accounts" ON amc_instances
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM amc_accounts 
            WHERE amc_accounts.id = amc_instances.account_id 
            AND amc_accounts.user_id = auth.uid()
        )
    );

-- Campaign mappings policies
CREATE POLICY "Users can view own campaigns" ON campaign_mappings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own campaigns" ON campaign_mappings
    FOR ALL USING (auth.uid() = user_id);

-- Brand configurations policies
-- Fixed: Using JSONB ? operator instead of ANY() for array checking
CREATE POLICY "Users can view own or shared brands" ON brand_configurations
    FOR SELECT USING (
        auth.uid() = owner_user_id OR 
        shared_with_users::jsonb ? auth.uid()::text
    );

CREATE POLICY "Only owners can insert brands" ON brand_configurations
    FOR INSERT WITH CHECK (auth.uid() = owner_user_id);

CREATE POLICY "Only owners can update brands" ON brand_configurations
    FOR UPDATE USING (auth.uid() = owner_user_id);

CREATE POLICY "Only owners can delete brands" ON brand_configurations
    FOR DELETE USING (auth.uid() = owner_user_id);

-- Workflows policies
CREATE POLICY "Users can view own workflows" ON workflows
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own workflows" ON workflows
    FOR ALL USING (auth.uid() = user_id);

-- Workflow executions policies
CREATE POLICY "Users can view executions for their workflows" ON workflow_executions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM workflows 
            WHERE workflows.id = workflow_executions.workflow_id 
            AND workflows.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage executions for their workflows" ON workflow_executions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM workflows 
            WHERE workflows.id = workflow_executions.workflow_id 
            AND workflows.user_id = auth.uid()
        )
    );

-- Workflow schedules policies
CREATE POLICY "Users can view schedules for their workflows" ON workflow_schedules
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM workflows 
            WHERE workflows.id = workflow_schedules.workflow_id 
            AND workflows.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage schedules for their workflows" ON workflow_schedules
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM workflows 
            WHERE workflows.id = workflow_schedules.workflow_id 
            AND workflows.user_id = auth.uid()
        )
    );

-- Query templates policies
CREATE POLICY "Users can view own or public templates" ON query_templates
    FOR SELECT USING (
        auth.uid() = user_id OR is_public = true
    );

CREATE POLICY "Users can manage own templates" ON query_templates
    FOR ALL USING (auth.uid() = user_id);

-- AMC query results policies
CREATE POLICY "Users can view own query results" ON amc_query_results
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own query results" ON amc_query_results
    FOR ALL USING (auth.uid() = user_id);

-- Additional admin policies (optional)
-- These allow admin users to manage all data
CREATE POLICY "Admins can view all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.is_admin = true
        )
    );

CREATE POLICY "Admins can view all campaigns" ON campaign_mappings
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.is_admin = true
        )
    );

CREATE POLICY "Admins can view all workflows" ON workflows
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = auth.uid() 
            AND users.is_admin = true
        )
    );