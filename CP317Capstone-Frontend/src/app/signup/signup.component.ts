import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './signup.component.html',
  styleUrls: ['./signup.component.css']
})
export class SignupComponent implements OnInit {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);
  private router = inject(Router);

  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  showConsentModal = signal(true);

  signupForm = this.fb.group({
    fullName: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
    confirmPassword: ['', [Validators.required]]
  }, { validators: this.passwordMatchValidator });

  ngOnInit() {
    // Show modal automatically on entering signup page
    this.showConsentModal.set(true);
  }

  onAcceptConsent() {
    this.api.consent('accept').subscribe({
      next: () => {
        this.showConsentModal.set(false);
      },
      error: () => {
        this.errorMessage.set('Failed to process consent.');
      }
    });
  }

  onDeclineConsent() {
    this.api.consent('decline').subscribe({
      next: () => {
        this.router.navigate(['']);
      },
      error: () => {
        this.router.navigate(['']);
      }
    });
  }

  private passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');
    if (password && confirmPassword && password.value !== confirmPassword.value) {
      confirmPassword.setErrors({ mismatch: true });
      return { mismatch: true };
    }
    return null;
  }

  onSubmit() {
    if (this.signupForm.invalid) {
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const { fullName, email, password } = this.signupForm.value;

    const payload = {
      name: fullName!,
      email: email!,
      password: password!,
      role: 'customer',
      preferred_category: 'general'
    };

    this.api.createAccount(payload).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        this.router.navigate(['/login']);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.error?.error || err.error?.message || 'Failed to create account. Please try again.');
      }
    });
  }
}