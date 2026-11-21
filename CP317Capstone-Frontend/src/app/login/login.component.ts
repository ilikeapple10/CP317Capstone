import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['../signup/signup.component.css', './login.component.css']
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private api = inject(ApiService);
  private router = inject(Router);

  isLoading = signal(false);
  errorMessage = signal<string | null>(null);
  captchaQuestion = signal('');

  loginForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(6)]],
    captcha: ['']
  });

  refreshCaptcha() {
    this.api.getCaptcha().subscribe({ next: (r) => { this.captchaQuestion.set(r.question); this.loginForm.patchValue({ captcha: '' }); } });
  }

  onSubmit() {
    if (this.loginForm.invalid) return;

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const { email, password, captcha } = this.loginForm.value;

    this.api.login(email!, password!, this.captchaQuestion() ? captcha! : undefined).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        this.router.navigate([res.user?.role === 'seller' ? '/seller' : '']);
      },
      error: (err) => {
        this.isLoading.set(false);
        if (err.status === 423) {
          this.errorMessage.set(err.error?.error || 'Account locked. Please try again later.');
          this.captchaQuestion.set('');
        } else {
          this.errorMessage.set(err.error?.error || err.error?.message || 'Invalid email or password. Please try again.');
          if (err.error?.require_captcha) {
            this.api.getCaptcha().subscribe({ next: (r) => { this.captchaQuestion.set(r.question); this.loginForm.patchValue({ captcha: '' }); } });
          }
        }
      }
    });
  }
}
