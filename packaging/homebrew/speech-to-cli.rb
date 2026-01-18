class SpeechToCli < Formula
  include Language::Python::Virtualenv

  desc "Push-to-talk speech recognition that types into any application"
  homepage "https://github.com/WindyBanana/speech-to-cli"
  url "https://github.com/WindyBanana/speech-to-cli/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"  # Update this when releasing
  license "MIT"

  depends_on "python@3.12"
  depends_on "portaudio"  # Required by sounddevice

  resource "numpy" do
    url "https://files.pythonhosted.org/packages/source/n/numpy/numpy-1.26.4.tar.gz"
    sha256 "2a02aba9ed12e4ac4eb3ea9421c420301a0c6460d9830d74a9df87efa4912010"
  end

  resource "sounddevice" do
    url "https://files.pythonhosted.org/packages/source/s/sounddevice/sounddevice-0.4.7.tar.gz"
    sha256 "1c3f18b318e3781e64e5b3c4c43d9e90fc2c99db2c7a3c2bb351e823a0c9a6a8"
  end

  resource "openai" do
    url "https://files.pythonhosted.org/packages/source/o/openai/openai-1.58.1.tar.gz"
    sha256 "PLACEHOLDER_SHA256"  # Update with actual sha256
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/source/p/python-dotenv/python_dotenv-1.0.1.tar.gz"
    sha256 "e324ee90a023d808f1959c46bcbc04446a10ced277783dc6ee09987c37ec10ca"
  end

  resource "pynput" do
    url "https://files.pythonhosted.org/packages/source/p/pynput/pynput-1.7.7.tar.gz"
    sha256 "PLACEHOLDER_SHA256"  # Update with actual sha256
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      To use speech-to-cli, you need to:

      1. Set your OpenAI API key:
         export OPENAI_API_KEY="your-api-key"

      2. Grant Accessibility permissions:
         System Preferences > Privacy & Security > Accessibility
         Add your terminal app (Terminal, iTerm2, etc.)

      3. Run the daemon:
         speech-to-cli

      For more options, see:
         speech-to-cli --help
    EOS
  end

  test do
    # Basic test that the command runs
    assert_match "usage:", shell_output("#{bin}/speech-to-cli --help")
  end
end
