#!/usr/bin/perl -w
# NMAScript, to communicate with the Notify My Android server.
#
# Copyright (c) 2010, Zachary West
# All rights reserved.
# Rafactoring to Notify My Android: Adriano Maia
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Zachary West nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY Zachary West ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Zachary West BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# NOTIFY MY ANDROID (NMA) IS NOT RELATED TO PROWL OR ZACHARY WEST. TWO SEPARATE PROJECTS WITH A SIMILAR API.
#
# This requires running Notify My Android on your device.
# See the NMA website <http://www.notifymyandroid.com>
#

use strict;
use LWP::UserAgent;
use Getopt::Long;
use Pod::Usage;

# Grab our options.
my %options = ();
GetOptions(\%options, 'apikey=s', 'apikeyfile=s',
					  'developerkey=s', 
					  'application=s', 'event=s', 'notification=s',
					  'priority:i', 'help|?') or pod2usage(2);

$options{'application'} ||= "NMAScript";
$options{'priority'} ||= 0;

pod2usage(-verbose => 2) if (exists($options{'help'}));
pod2usage(-message => "$0: Event name is required") if (!exists($options{'event'}));
pod2usage(-message => "$0: Notification text is required") if (!exists($options{'notification'}));
pod2usage(-priority => "$0: Priority must be in the range [-2, 2]") if ($options{'priority'} < -2 || $options{'priority'} > 2);

# Get the API key from STDIN if one isn't provided via a file or from the command line.
if (!exists($options{'apikey'}) && !exists($options{'apikeyfile'})) {
	print "API key: ";

	$options{'apikey'} = <STDIN>;
	chomp $options{'apikey'};
} elsif (exists($options{'apikeyfile'})) {
	open(APIKEYFILE, $options{'apikeyfile'}) or die($!);
	$options{'apikey'} = <APIKEYFILE>;
	close(APIKEYFILE);
	
	chomp $options{'apikey'};
}

# URL encode our arguments
$options{'application'} =~ s/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg;
$options{'event'} =~ s/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg;
$options{'notification'} =~ s/([^A-Za-z0-9])/sprintf("%%%02X", ord($1))/seg;

# Generate our HTTP request.
my ($userAgent, $request, $response, $requestURL);
$userAgent = LWP::UserAgent->new;
$userAgent->agent("NMAScript/1.0");
$userAgent->env_proxy();

my $developerKeyString = "";
if(exists($options{'developerkey'})) {
	$developerKeyString = sprintf("&developerkey=%s", $options{'developerkey'});
}

$requestURL = sprintf("https://www.notifymyandroid.com/publicapi/notify?apikey=%s&application=%s&event=%s&description=%s&priority=%d%s",
				$options{'apikey'},
				$options{'application'},
				$options{'event'},
				$options{'notification'},
				$options{'priority'},
				$developerKeyString);

$request = HTTP::Request->new(GET => $requestURL);

$response = $userAgent->request($request);

if ($response->is_success) {
	print "Notification successfully posted.\n";
} else {
	print STDERR "Notification not posted: " . $response->content . "\n";
}

__END__

=head1 NAME 

nma - Send NotifyMyAndroid notifications

=head1 SYNOPSIS

nma.pl [options] event_information

 Options:
   -help              Display all help information.
   -apikey=...        Your NotifyMyAndroid API key.
   -apikeyfile=...    A file containing your NMA API key.
   -developerkey=...   Your developer key (optional)

 Event information:
   -application=...   The name of the application.
   -event=...         The name of the event.
   -notification=...  The text of the notification.
   -priority=...      The priority of the notification.
                      An integer in the range [-2, 2].

=head1 OPTIONS

=over 8

=item B<-apikey>

Your NMA API key. It is not recommend you use this, use the apikeyfile option.

=item B<-developerkey>

Your NMA developer key. This is an optional argument, and should be used if you were provided one for whitelisting reasons.

=item B<-apikeyfile>

A file containing one line, which has your NMA API key on it.

=item B<-application>

The name of the Application part of the notification. If none is provided, NMAScript is used.

=item B<-event>

The name of the Event part of the notification. This is generally the action which occurs, such as "disk partitioning completed."

=item B<-notification>

The text of the notification, which has more details for a particular event. This is generally the description of the action which occurs, such as "The disk /dev/abc was successfully partitioned."

=item B<-priority>

The priority level of the notification. An integer value ranging [-2, 2] with meanings Very Low, Moderate, Normal, High, Emergency.

=back

=head1 DESCRIPTION

B<This program> sends a notification to the NMA server, which is then forwarded to your device running the NMA application.

=head1 HELP

For more assistance, visit the NMA website at <http://www.notifymyandroid.com>.

=cut
