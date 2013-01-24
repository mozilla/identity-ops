sudo true && curl -L https://www.opscode.com/chef/install.sh | sudo bash
sudo yum install -y git
sudo mkdir -p /var/chef/cookbooks
sudo chown root:wheel /var/chef/cookbooks
sudo chmod g+w /var/chef/cookbooks
cd /var/chef/cookbooks
git init
touch .gitignore
git add .gitignore
git commit -m "initial commit"
knife cookbook site install chef-server
cat > ~/chef-server.json <<End-of-message
{
  "chef_server": {
    "server_url": "http://localhost:4000",
    "webui_enabled": true
  },
  "run_list": [ "recipe[chef-server::rubygems-install]" ]
}
End-of-message
# manually fix OHAI-368 by modifing /var/chef/cookbooks/chef-server/recipes/rubygems-install.rb
sudo chef-solo -j ~/chef-server.json -r http://s3.amazonaws.com/chef-solo/bootstrap-latest.tar.gz
