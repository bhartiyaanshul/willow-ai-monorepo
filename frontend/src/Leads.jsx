import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './leads.css';

function Leads() {
    const [leads, setLeads] = useState([]);
    const [selected, setSelected] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        const stored = localStorage.getItem('willow_leads');
        setLeads(stored ? JSON.parse(stored) : []);
    }, []);

    const handleDelete = (idx) => {
        const updated = leads.filter((_, i) => i !== idx);
        setLeads(updated);
        localStorage.setItem('willow_leads', JSON.stringify(updated));
        if (selected === idx) setSelected(null);
    };

    function getParsedLead(selectedLead) {
        if (!selectedLead) return selectedLead;
        let parsed = { ...selectedLead };
        if (typeof selectedLead.summary === 'string' && selectedLead.summary.trim().startsWith('```json')) {
            try {
                const jsonStr = selectedLead.summary.replace(/^```json/, '').replace(/```$/, '').trim();
                parsed = { ...parsed, ...JSON.parse(jsonStr) };
            } catch (e) { }
        }
        return parsed;
    }

    const parsedLeads = leads.map(getParsedLead);

    return (
        <div className="leads-container">
            <div className="leads-sidebar-fixed">
                <div className="sidebar-header">
                    <div className="logo">Willow Leads Dashboard</div>
                </div>
                <div className="lead-items">
                    {parsedLeads.length === 0 ? (
                        <div className="empty">No leads found</div>
                    ) : (
                        parsedLeads.map((lead, idx) => (
                            <div
                                key={idx}
                                className={`lead-card ${selected === idx ? 'selected' : ''} ${lead.critical ? 'critical' : ''}`}
                                onClick={() => setSelected(idx)}
                            >
                                <div className="lead-title-row">
                                    <span className="company-name">{lead.company || 'Untitled'}</span>
                                    {lead.critical && <span className="critical-dot">●</span>}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
            <div className="leads-details">
                {selected !== null && parsedLeads[selected] ? (
                    (() => {
                        const lead = parsedLeads[selected];
                        return (
                            <div className="details-card">
                                <div className="header-row">
                                    <h3 className='company-name'>{lead.company || 'Untitled Company'}</h3>
                                    <button className="delete-btn" onClick={() => handleDelete(selected)}>✕</button>
                                </div>
                                <div className="detail"><strong>Domain:</strong> {lead.domain || 'N/A'}</div>
                                <div className="detail"><strong>Budget:</strong> {lead.budget ? `$${lead.budget}` : 'N/A'}</div>
                                <div className="detail"><strong>Problem:</strong><div className="box">{lead.problem}</div></div>
                                <div className="detail"><strong>Status:</strong> {lead.status || 'Discovery'}</div>
                                <div className="detail"><strong>Summary:</strong><div className="box">{lead.summary || 'N/A'}</div></div>
                                {lead.agent_summary && <div className="detail"><strong>Agent Notes:</strong><div className="box">{lead.agent_summary}</div></div>}
                                <div className="detail"><strong>Last User Message:</strong><div className="box">{lead.user_last_message || 'N/A'}</div></div>
                            </div>
                        );
                    })()
                ) : (
                    <div className="placeholder">Select a lead to view details.</div>
                )}
            </div>
        </div>
    );
}

export default Leads;
