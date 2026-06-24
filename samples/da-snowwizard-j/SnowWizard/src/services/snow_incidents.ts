//Uses the ServiceNow Rest API to deal with incidents
//Author: crisag@microsoft.com

import axios from 'axios';
import * as dotenv from 'dotenv';

dotenv.config({ path: 'env/.env.local.user' });

class IncidentsApiService {
    
    private SN_INSTANCE: string;
    private SN_USERNAME: string;
    private SN_PASSWORD: string;

    constructor() {
        // Environment variables setup
        this.SN_INSTANCE = process.env.SN_INSTANCE || '';
        this.SN_USERNAME = process.env.SN_USERNAME || '';
        this.SN_PASSWORD = process.env.SN_PASSWORD || '';
    }

    // Function to fetch a single incident from ServiceNow
    async getIncident(id: string) {
    try {
        const response = await axios.get(
        `https://${this.SN_INSTANCE}.service-now.com/api/now/table/incident`,
        {
            params: {
            sysparm_limit: 1,
            sysparm_fields: 'number,made_sla,short_description,description,priority,opened_at',
            sysparm_query: `number=${id}`
            },
            auth: {
            username: this.SN_USERNAME,
            password: this.SN_PASSWORD
            },
            headers: {
            'Content-Type': 'application/json',
            },
        }
        );
        console.log('Incidents fetched successfully from ServiceNow:', response.data.result);
        // Extracting incidents from response
        return response.data.result;
    } catch (error) {
        console.error('Error fetching incidents:', error);
        throw error;
    }
    }

    // Function to fetch the latest 10 incidents from ServiceNow
    async getIncidents() {
    try {
        const response = await axios.get(
        `https://${this.SN_INSTANCE}.service-now.com/api/now/table/incident`,
        {
            params: {
            sysparm_limit: 10,
            sysparm_fields: 'number,made_sla,short_description,description,priority,opened_at',
            sysparm_query: 'ORDERBYDESCsys_created_on'
            },
            auth: {
            username: this.SN_USERNAME,
            password: this.SN_PASSWORD
            },
            headers: {
            'Content-Type': 'application/json',
            },
        }
        );
        console.log('Incidents fetched successfully from ServiceNow:', response.data.result);
        // Extracting incidents from response
        return response.data.result;
    } catch (error) {
        console.error('Error fetching incidents:', error);
        throw error;
    }
    }

    // Function to fetch the latest 10 incidents from ServiceNow
    async getUserIncidents(username: string) {
        try {
            //get the sys_id of the user
            const sys_id = await this.getUserSysId(username);
            //fetch incidents assigned to the user
            const response = await axios.get(
            `https://${this.SN_INSTANCE}.service-now.com/api/now/table/incident`,
            {
                params: {
                sysparm_limit: 10,
                sysparm_fields: 'number,made_sla,short_description,description,priority,opened_at',
                sysparm_query: `ORDERBYDESCsys_created_on^assigned_to=${sys_id}`
                },
                auth: {
                username: this.SN_USERNAME,
                password: this.SN_PASSWORD
                },
                headers: {
                'Content-Type': 'application/json',
                },
            }
            );
            console.log('Incidents fetched successfully from ServiceNow:', response.data.result);
            // Extracting incidents from response
            return response.data.result;
        } catch (error) {
            console.error('Error fetching incidents:', error);
            throw error;
        }
        }

        // Function to create a new incident in ServiceNow
        async createIncident(email: string, short_description: string, description: string) {
            try {
                //get the sys_id of the user
                const sys_id = await this.getUserSysId(email);
                // Create a new incident on Service Now
                const response = await axios.post(
                `https://${this.SN_INSTANCE}.service-now.com/api/now/table/incident`,
                {
                    short_description: `${short_description}`,
                    description: `${description}`,
                    caller_id: sys_id
                },
                {
                    auth: {
                    username: this.SN_USERNAME,
                    password: this.SN_PASSWORD
                    },
                    headers: {
                    'Content-Type': 'application/json',
                    },
                }
                );
                console.log('Incident created successfully in ServiceNow:', response.data.result);
                // Extracting incident from response
                return response.data.result;
            } catch (error) {
                console.error('Error creating incident:', error);
                throw error;
            }
        }

        private async getUserSysId(username: string) {
            const response = await axios.get(
                `https://${this.SN_INSTANCE}.service-now.com/api/now/table/sys_user`,
                {
                    params: {
                    sysparm_limit: 10,
                    sysparm_query: `email=${username}`
                    },
                    auth: {
                    username: this.SN_USERNAME,
                    password: this.SN_PASSWORD
                    },
                    headers: {
                    'Content-Type': 'application/json',
                    },
                }
                );
                console.log('User fetched successfully from ServiceNow:', response.data.result);
                // Extracting user sys_id from response
                return response.data.result[0].sys_id;
        }

}

export default new IncidentsApiService();

