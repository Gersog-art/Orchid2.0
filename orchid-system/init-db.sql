-- Incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id VARCHAR(50) UNIQUE NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    source_ip INET NOT NULL,
    request_url TEXT NOT NULL,
    request_method VARCHAR(10) NOT NULL,
    request_headers JSONB,
    request_body TEXT,
    ml_scores JSONB NOT NULL DEFAULT '{}',
    if_anomaly_score FLOAT,
    rf_prediction VARCHAR(50),
    rf_confidence FLOAT,
    final_verdict VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by UUID
);

-- Actions table
CREATE TABLE IF NOT EXISTS incident_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    action_type VARCHAR(20) NOT NULL,
    action_value TEXT,
    performed_by VARCHAR(100),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reverted BOOLEAN DEFAULT FALSE,
    revert_reason TEXT
);

-- Blocklist table
CREATE TABLE IF NOT EXISTS ip_blocklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address INET UNIQUE NOT NULL,
    incident_id UUID REFERENCES incidents(id),
    blocked_by VARCHAR(100),
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- Whitelist table
CREATE TABLE IF NOT EXISTS ip_whitelist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address INET UNIQUE NOT NULL,
    added_by VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Watchlist table
CREATE TABLE IF NOT EXISTS ip_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address INET NOT NULL,
    incident_count INTEGER DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    risk_score INTEGER DEFAULT 1
);

-- Create indexes for performance
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_created_at ON incidents(created_at DESC);
CREATE INDEX idx_incidents_source_ip ON incidents(source_ip);
CREATE INDEX idx_ip_blocklist_active ON ip_blocklist(is_active, expires_at);
CREATE INDEX idx_ip_watchlist_risk ON ip_watchlist(risk_score DESC, last_seen DESC);

-- Create function to automatically update watchlist
CREATE OR REPLACE FUNCTION update_watchlist()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.final_verdict = 'attack' THEN
        INSERT INTO ip_watchlist (ip_address, incident_count, last_seen, risk_score)
        VALUES (NEW.source_ip, 1, NEW.created_at, 1)
        ON CONFLICT (ip_address) 
        DO UPDATE SET 
            incident_count = ip_watchlist.incident_count + 1,
            last_seen = NEW.created_at,
            risk_score = ip_watchlist.risk_score + 1;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for watchlist updates
CREATE TRIGGER trigger_update_watchlist
AFTER INSERT ON incidents
FOR EACH ROW
EXECUTE FUNCTION update_watchlist();
