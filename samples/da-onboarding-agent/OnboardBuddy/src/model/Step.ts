export interface Step {
    stepId: string;             // Unique identifier for this step; can be used for correlating step completion
    isCurrent: boolean;         // True if this is the current step
    isLast: boolean;            // True if this is the last step
    stepNumber: number;         // Sequence number for display to users
    name: string;               // Task name
    description: string;        // Task description
    resourceUrl: string;        // URL of resource to be used to complete the task
}

export interface CompletedStep {
    stepId: string;             // Unique identifier for this step
}