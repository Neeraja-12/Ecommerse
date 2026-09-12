from django import forms
from .models import UserAddress
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# Common Tailwind classes for inputs
TAILWIND_INPUT_CLASSES = "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
TAILWIND_TEXTAREA_CLASSES = "w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24 resize-none"

class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form with Tailwind styling
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Enter your email'
        })
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Choose a username'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Enter password'
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class AddressForm(forms.ModelForm):
    """
    Form for creating and updating user addresses
    """
    # Add this field for new addresses in checkout
    save_address = forms.BooleanField(
        required=False,
        initial=True,
        label='Save this address for future orders',
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
    )
    
    class Meta:
        model = UserAddress
        fields = ['full_name', 'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'phone_number', 'is_default']  # CHANGED: 'default' to 'is_default'
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Full Name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Phone Number'
            }),
            'address_line1': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Address Line 1'
            }),
            'address_line2': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Address Line 2 (Optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'State'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Postal Code'
            }),
            'country': forms.TextInput(attrs={
                'class': TAILWIND_INPUT_CLASSES,
                'placeholder': 'Country'
            }),
            'is_default': forms.CheckboxInput(attrs={  # CHANGED: 'default' to 'is_default'
                'class': 'mr-2'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make is_default field optional in forms
        self.fields['is_default'].required = False  # CHANGED: 'default' to 'is_default'

class CheckoutForm(forms.Form):
    """
    Form for checkout process - payment method selection
    """
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debbit Card'),
        ('paypal', 'PayPal'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('gpay', 'GPay'),
        ('phonepe', 'PhonePe'),
        ('paytm', 'Paytm'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-2 payment-method-radio'
        }),
        label="Choose Your Payment Method",
        initial='credit_card'
    )

class PaymentMethodForm(forms.Form):
    """
    Alternative payment method form (can be used in different contexts)
    """
    PAYMENT_METHOD_CHOICES = [
        ('gpay', 'GPay'),
        ('phonepe', 'PhonePe'),
        ('paytm', 'Paytm'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'mb-2 payment-method-radio'
        }),
        label="Choose Your Payment Method"
    )

class NewsletterForm(forms.Form):
    """
    Form for newsletter subscription
    """
    email = forms.EmailField(
        label='',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Enter your email address'
        })
    )

class ShippingInfoForm(forms.Form):
    """
    Standalone shipping information form (alternative to UserAddressForm)
    """
    full_name = forms.CharField(
        max_length=100, 
        label="Full Name",
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Full Name'
        })
    )
    phone_number = forms.CharField(
        max_length=15, 
        label="Phone Number",
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Phone Number'
        })
    )
    address_line1 = forms.CharField(
        max_length=255, 
        label="Address Line 1",
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Address Line 1'
        })
    )
    address_line2 = forms.CharField(
        max_length=255, 
        label="Address Line 2", 
        required=False,
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Address Line 2 (Optional)'
        })
    )
    city = forms.CharField(
        max_length=100, 
        label="City",
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'City'
        })
    )
    state = forms.CharField(
        max_length=100, 
        label="State",
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'State'
        })
    )
    postal_code = forms.CharField(
        max_length=20, 
        label="Postal Code",
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Postal Code'
        })
    )
    country = forms.CharField(
        max_length=50, 
        label="Country",
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Country'
        })
    )
    save_address = forms.BooleanField(
        required=False,
        initial=True,
        label='Save this shipping address',
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
    )

class ProductSearchForm(forms.Form):
    """
    Form for product search functionality
    """
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Search products...'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Categories'),
            ('electronics', 'Electronics'),
            ('jewelery', 'Fashion'),
            ('home', 'Home'),
            ('books', 'Books'),
            ('toys', 'Toys'),
            ('sports', 'Sports'),
        ],
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )

class ContactForm(forms.Form):
    """
    Contact form for customer support
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Your Email'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASSES,
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': TAILWIND_TEXTAREA_CLASSES,
            'placeholder': 'Your message...',
            'rows': 5
        })
    )

class CartUpdateForm(forms.Form):
    """
    Form for updating cart item quantities
    """
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            'class': 'w-20 px-2 py-1 border rounded text-center',
            'min': '1',
            'max': '10'
        })
    )

class ReviewForm(forms.Form):
    """
    Form for product reviews and ratings
    """
    RATING_CHOICES = [
        (5, '★★★★★'),
        (4, '★★★★☆'),
        (3, '★★★☆☆'),
        (2, '★★☆☆☆'),
        (1, '★☆☆☆☆'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'flex space-x-2'
        }),
        label="Your Rating"
    )
    
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': TAILWIND_TEXTAREA_CLASSES,
            'placeholder': 'Write your review... (optional)',
            'rows': 4
        })
    )

class CouponForm(forms.Form):
    """
    Form for applying discount coupons
    """
    coupon_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter coupon code'
        })
    )