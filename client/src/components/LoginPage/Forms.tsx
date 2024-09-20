import React, { useState } from 'react';
import { useLoginMutation, useSignUpMutation } from '../../api';
import ErrorView from '../ErrorView';

type OnSwitchFormProp = {
    onSwitchForm: () => void;
};

type OnSubmit = (username: string, password: string, confirmPassword?: string) => void;

type FormProps = OnSwitchFormProp & {
    isLoginForm: boolean;
    isLoading: boolean;
    onSubmit: OnSubmit;
    verifyError: string | null;
    error: unknown,
};

function Form({ isLoginForm, isLoading, onSubmit: customOnSubmit, onSwitchForm, verifyError, error }: FormProps) {
    const onSubmit = (formEvent: React.FormEvent) => {
        formEvent.preventDefault();
        const formData = new FormData(formEvent.target as HTMLFormElement);
        const username = formData.get('username') as string;
        const password = formData.get('password') as string;
        const confirmPassword = formData.get('confirm-password') as string;
        customOnSubmit(username, password, confirmPassword);
    };

    const errorViewProps = isLoginForm ? { loginForm: error } : { submitForm : error };
    const passwordAutoComplete = isLoginForm ? "current-password" : "new-password";
    return <>
        <form onSubmit={onSubmit}>
            <input type="text" name="username" placeholder="username" autoComplete="username" />
            <input type="password" name="password" placeholder="password" autoComplete={passwordAutoComplete} />
            {isLoginForm ? <></> : <input type="password" name="confirm-password" placeholder="confirm password" autoComplete={passwordAutoComplete} />}
            <button onClick={onSwitchForm}>{isLoginForm ? "Sign Up" : "Cancel"}</button>
            <button type="submit">{isLoginForm ? "Log In" : "Sign Up"}</button>
        </form>
        {verifyError !== null ? <p>{verifyError}</p> : <></>}
        <ErrorView {...errorViewProps} />
        {isLoading ? <p>Loading...</p> : <></>}
    </>;
}

export function SignUpForm({ onSwitchForm }: OnSwitchFormProp) {
    const [ triggerSignUp, { isLoading: isSignUpLoading, error: signUpError, reset: resetSignUpMutation } ] = useSignUpMutation();
    const [ verifyError, setVerifyError ] = useState<string | null>(null);

    const onSignUp: OnSubmit = async (username, password, confirmPassword) => {
        if (password === confirmPassword) {
            setVerifyError(null);
            const { error } = await triggerSignUp({ username, password });
            if (!error) onSwitchForm();
        } else {
            setVerifyError('passwords do not match');
            resetSignUpMutation();
        }
    };

    return <Form
        isLoginForm={false}
        isLoading={isSignUpLoading}
        onSubmit={onSignUp}
        onSwitchForm={onSwitchForm}
        verifyError={verifyError}
        error={signUpError}
    />;
}

export function LoginForm({ onSwitchForm }: OnSwitchFormProp) {
    const [ triggerLogin, { isLoading: isLoginLoading, error: loginError } ] = useLoginMutation();

    const onLogin: OnSubmit = (username, password) => {
        triggerLogin({ username, password });
    }

    return <Form
        isLoginForm={true}
        isLoading={isLoginLoading}
        onSubmit={onLogin}
        onSwitchForm={onSwitchForm}
        verifyError={null}
        error={loginError}
    />
}
