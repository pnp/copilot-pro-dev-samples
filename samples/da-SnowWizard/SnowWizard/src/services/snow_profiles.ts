//Uses the ServiceNow Rest API to deal with profile information
//Author: crisag@microsoft.com

import axios from 'axios';
import * as dotenv from 'dotenv';

dotenv.config({ path: 'env/.env.local.user' });

class ProfilesApiService {
    
    private SN_INSTANCE: string;
    private SN_USERNAME: string;
    private SN_PASSWORD: string;

    constructor() {
        // Environment variables setup
        this.SN_INSTANCE = process.env.SN_INSTANCE || '';
        this.SN_USERNAME = process.env.SN_USERNAME || '';
        this.SN_PASSWORD = process.env.SN_PASSWORD || '';
    }

    // Function to fetch the latest 10 incidents from ServiceNow
    async getProfile(email: string) {
    try {
        const response = await axios.get(
        `https://${this.SN_INSTANCE}.service-now.com/api/now/table/sys_user`,
        {
            params: {
            sysparm_limit: 10,
            sysparm_query: `email=${email}`
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
        console.log('Profile fetched successfully from ServiceNow:', response.data.result);
        return response.data.result;
    } catch (error) {
        console.error('Error fetching profile:', error);
        throw error;
    }
    }


}

export default new ProfilesApiService();

